from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import func, extract, and_, or_, text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.db.orm_models import Apontamento, Recurso, Projeto, Equipe, Secao, FonteApontamento
from app.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)

class ApontamentoRepository(BaseRepository[Apontamento]):
    """
    Repositório para operações específicas de apontamentos de horas.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa o repositório com uma sessão do banco de dados.
        
        Args:
            db: Sessão do banco de dados assíncrona
        """
        super().__init__(db, Apontamento)
    
    async def get_by_jira_worklog_id(self, jira_worklog_id: str) -> Optional[Apontamento]:
        """Obtém um apontamento pelo ID do worklog do Jira."""
        query = select(Apontamento).filter(Apontamento.jira_worklog_id == jira_worklog_id)
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def create_manual(self, data: Dict[str, Any], admin_id: int) -> Apontamento:
        """
        Cria um apontamento manual feito por um administrador.
        
        Args:
            data: Dados do apontamento
            admin_id: ID do administrador que está criando o apontamento
            
        Returns:
            Apontamento criado
        """
        apontamento_data = {
            **data,
            "fonte_apontamento": "MANUAL",
            "id_usuario_admin_criador": admin_id
        }
        return await self.create(apontamento_data)
    
    async def update_manual(self, id: int, data: Dict[str, Any]) -> Optional[Apontamento]:
        """
        Atualiza um apontamento manual.
        
        Args:
            id: ID do apontamento
            data: Dados atualizados
            
        Returns:
            Apontamento atualizado ou None se não encontrado ou não for manual
        """
        apontamento = await self.get(id)
        if apontamento is None or apontamento.fonte_apontamento != "MANUAL":
            return None
            
        return await self.update(id, data)
    
    async def delete_manual(self, id: int) -> bool:
        """
        Remove um apontamento manual.
        
        Args:
            id: ID do apontamento
            
        Returns:
            True se removido com sucesso, False se não encontrado ou não for manual
        """
        apontamento = await self.get(id)
        if apontamento is None or apontamento.fonte_apontamento != "MANUAL":
            return False
            
        return await self.delete(id)
    
    async def sync_jira_apontamento(self, jira_worklog_id: str, data: Dict[str, Any]) -> Apontamento:
        """
        Cria ou atualiza um apontamento a partir de dados do Jira.
        
        Args:
            jira_worklog_id: ID do worklog no Jira
            data: Dados do apontamento
            
        Returns:
            Apontamento criado ou atualizado
        """
        logger.info(f"[SYNC_APONTAMENTO] Sincronizando apontamento para worklog_id={jira_worklog_id}")
        
        try:
            # Verificar se o apontamento já existe
            query = select(Apontamento).where(Apontamento.jira_worklog_id == jira_worklog_id)
            result = await self.db.execute(query)
            apontamento = result.scalars().first()
            
            # Remover timezone de todos os campos datetime (se houver)
            for campo in ["data_hora_inicio_trabalho", "data_criacao", "data_atualizacao", "data_sincronizacao_jira"]:
                valor = data.get(campo)
                if isinstance(valor, datetime) and valor.tzinfo is not None:
                    data[campo] = valor.replace(tzinfo=None)
            
            # Garantir que fonte_apontamento seja do tipo correto (enum)
            data["fonte_apontamento"] = FonteApontamento.JIRA
            
            # Verificar se temos todos os campos obrigatórios
            campos_obrigatorios = [
                "recurso_id", "projeto_id", "data_apontamento", 
                "horas_apontadas", "data_criacao", "data_atualizacao"
            ]
            
            for campo in campos_obrigatorios:
                if campo not in data or data[campo] is None:
                    logger.error(f"[SYNC_APONTAMENTO] Campo obrigatório ausente: {campo}")
                    raise ValueError(f"Campo obrigatório ausente: {campo}")
            
            if apontamento:
                logger.info(f"[SYNC_APONTAMENTO] Atualizando apontamento existente id={apontamento.id}")
                # Atualiza o apontamento existente
                for key, value in data.items():
                    setattr(apontamento, key, value)
                    
                await self.db.commit()
                await self.db.refresh(apontamento)
                logger.info(f"[SYNC_APONTAMENTO] Apontamento atualizado com sucesso id={apontamento.id}")
                return apontamento
            else:
                logger.info(f"[SYNC_APONTAMENTO] Criando novo apontamento para worklog_id={jira_worklog_id}")
                # Cria um novo apontamento
                apontamento = self.model(**data)
                self.db.add(apontamento)
                await self.db.commit()
                await self.db.refresh(apontamento)
                logger.info(f"[SYNC_APONTAMENTO] Apontamento criado com sucesso id={apontamento.id}")
                return apontamento
                
        except Exception as e:
            logger.error(f"[SYNC_APONTAMENTO] Erro ao sincronizar apontamento: {str(e)}")
            await self.db.rollback()
            raise
    
    async def delete_from_jira(self, jira_worklog_id: str) -> bool:
        """
        Remove um apontamento com base no ID do worklog do Jira.
        
        Args:
            jira_worklog_id: ID do worklog no Jira
            
        Returns:
            True se removido com sucesso, False se não encontrado
        """
        query = select(Apontamento).filter(Apontamento.jira_worklog_id == jira_worklog_id)
        result = await self.db.execute(query)
        apontamento = result.scalars().first()
        
        if apontamento is None:
            return False
            
        await self.db.delete(apontamento)
        await self.db.commit()
        return True
    
    async def find_with_filters(self, 
                        recurso_id: Optional[int] = None,
                        projeto_id: Optional[int] = None,
                        equipe_id: Optional[int] = None,
                        secao_id: Optional[int] = None,
                        data_inicio: Optional[date] = None,
                        data_fim: Optional[date] = None,
                        fonte_apontamento: Optional[str] = None,
                        jira_issue_key: Optional[str] = None,
                        skip: int = 0,
                        limit: int = 100
                       ) -> List[Apontamento]:
        """Busca apontamentos com filtros avançados."""
        query = select(Apontamento)
        
        # Aplicar filtros diretos
        if recurso_id:
            query = query.filter(Apontamento.recurso_id == recurso_id)
        
        if projeto_id:
            query = query.filter(Apontamento.projeto_id == projeto_id)
        
        if data_inicio:
            query = query.filter(Apontamento.data_apontamento >= data_inicio)
        
        if data_fim:
            query = query.filter(Apontamento.data_apontamento <= data_fim)
        
        if fonte_apontamento:
            query = query.filter(Apontamento.fonte_apontamento == fonte_apontamento)
        
        if jira_issue_key:
            query = query.filter(Apontamento.jira_issue_key.ilike(f"%{jira_issue_key}%"))
        
        # Filtros relacionais (equipe e seção)
        if equipe_id or secao_id:
            query = query.join(Apontamento.recurso)
            
            if equipe_id:
                query = query.filter(Recurso.equipe_principal_id == equipe_id)
            
            if secao_id:
                query = query.join(Recurso.equipe_principal).filter(Equipe.secao_id == secao_id)
        
        # Aplicar paginação e ordenação
        result = await self.db.execute(query.order_by(Apontamento.data_apontamento.desc()).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def find_with_filters_and_aggregate(
        self,
        recurso_id: Optional[int] = None,
        projeto_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        fonte_apontamento: Optional[str] = None,
        jira_issue_key: Optional[str] = None,
        agrupar_por_recurso: bool = False,
        agrupar_por_projeto: bool = False,
        agrupar_por_data: bool = False,
        agrupar_por_mes: bool = True,
        aggregate: bool = False
    ) -> Dict[str, Any]:
        """
        Busca apontamentos com filtros avançados e opcionalmente agrega horas.
        Corrigido para evitar JOIN duplo em recurso/equipe.
        
        Args:
            recurso_id: Filtro por recurso
            projeto_id: Filtro por projeto
            equipe_id: Filtro por equipe do recurso
            secao_id: Filtro por seção do recurso
            data_inicio: Data inicial do período
            data_fim: Data final do período
            fonte_apontamento: Filtro por fonte (MANUAL ou JIRA)
            jira_issue_key: Filtro por chave de issue no Jira
            aggregate: Se True, inclui agregações de horas
            
        Returns:
            Dicionário com resultados e agregações
        """
        query = select(self.model)
        
        # joinedload para agrupamento
        if agrupar_por_recurso:
            query = query.options(joinedload(self.model.recurso))
        if agrupar_por_projeto:
            query = query.options(joinedload(self.model.projeto))
        
        # Flags para controlar se join já foi feito
        recurso_joined = False
        equipe_joined = False

        # JOIN em Recurso se necessário para qualquer filtro relacional
        if any([equipe_id, secao_id]):
            query = query.join(Recurso, self.model.recurso_id == Recurso.id, isouter=False)
            recurso_joined = True
        
        # JOIN em Equipe se necessário para filtro de seção
        if secao_id:
            query = query.join(Equipe, Recurso.equipe_principal_id == Equipe.id, isouter=False)
            equipe_joined = True

        # Filtros diretos
        if recurso_id:
            query = query.filter(self.model.recurso_id == recurso_id)
        if projeto_id:
            query = query.filter(self.model.projeto_id == projeto_id)
        if equipe_id:
            # Se já fez join em Recurso, só filtra
            query = query.filter(Recurso.equipe_principal_id == equipe_id)
        if secao_id:
            # Se já fez join em Equipe, só filtra
            query = query.filter(Equipe.secao_id == secao_id)
        if data_inicio:
            query = query.filter(self.model.data_apontamento >= data_inicio)
        if data_fim:
            query = query.filter(self.model.data_apontamento <= data_fim)
        if fonte_apontamento:
            query = query.filter(self.model.fonte_apontamento == fonte_apontamento)
        if jira_issue_key:
            query = query.filter(self.model.jira_issue_key == jira_issue_key)
            
        try:
            result = await self.db.execute(query)
            apontamentos = result.scalars().all()
            
            # Se não há apontamentos, retornar estrutura vazia
            if not apontamentos:
                return {
                    "items": [],
                    "total": 0,
                    "total_horas": 0
                }
            
            # Se não há opções de agrupamento, retorna os apontamentos diretamente
            if not any([agrupar_por_recurso, agrupar_por_projeto, agrupar_por_data, agrupar_por_mes]):
                # Converter apontamentos para dicionários para evitar problemas de serialização
                apontamentos_dict = []
                for a in apontamentos:
                    apontamento_dict = {
                        "id": a.id,
                        "recurso_id": a.recurso_id,
                        "projeto_id": a.projeto_id,
                        "data_apontamento": a.data_apontamento.isoformat() if a.data_apontamento else None,
                        "horas_apontadas": float(a.horas_apontadas) if a.horas_apontadas else 0,
                        "descricao": a.descricao,
                        "fonte_apontamento": a.fonte_apontamento
                    }
                    apontamentos_dict.append(apontamento_dict)
                
                return {
                    "items": apontamentos_dict,
                    "total": len(apontamentos_dict),
                    "total_horas": sum(a["horas_apontadas"] for a in apontamentos_dict)
                }
            
            # Processar agrupamentos
            resultado_agrupado = []
            
            # Agrupar apontamentos
            grupos = {}
            for apontamento in apontamentos:
                try:
                    # Definir a chave de agrupamento
                    key_parts = []
                    
                    if agrupar_por_recurso and apontamento.recurso_id is not None:
                        key_parts.append(f"recurso_{apontamento.recurso_id}")
                    
                    if agrupar_por_projeto and apontamento.projeto_id is not None:
                        key_parts.append(f"projeto_{apontamento.projeto_id}")
                    
                    if agrupar_por_data and apontamento.data_apontamento is not None:
                        key_parts.append(f"data_{apontamento.data_apontamento.isoformat()}")
                    
                    if agrupar_por_mes and not agrupar_por_data and apontamento.data_apontamento is not None:
                        key_parts.append(f"ano_mes_{apontamento.data_apontamento.year}_{apontamento.data_apontamento.month}")
                    
                    # Se não há chave de agrupamento, usar "todos"
                    if not key_parts:
                        key = "todos"
                    else:
                        key = "_".join(key_parts)
                    
                    # Inicializar grupo se não existir
                    if key not in grupos:
                        grupo = {
                            "horas": 0,
                            "quantidade": 0
                        }
                        
                        # Adicionar informações de agrupamento
                        if agrupar_por_recurso and apontamento.recurso_id is not None:
                            grupo["recurso_id"] = apontamento.recurso_id
                            # Tentar obter o nome do recurso se disponível
                            if hasattr(apontamento, "recurso") and apontamento.recurso is not None:
                                grupo["recurso_nome"] = apontamento.recurso.nome
                        
                        if agrupar_por_projeto and apontamento.projeto_id is not None:
                            grupo["projeto_id"] = apontamento.projeto_id
                            # Tentar obter o nome do projeto se disponível
                            if hasattr(apontamento, "projeto") and apontamento.projeto is not None:
                                grupo["projeto_nome"] = apontamento.projeto.nome
                        
                        if agrupar_por_data and apontamento.data_apontamento is not None:
                            grupo["data"] = apontamento.data_apontamento.isoformat()
                        
                        if agrupar_por_mes and not agrupar_por_data and apontamento.data_apontamento is not None:
                            grupo["ano"] = apontamento.data_apontamento.year
                            grupo["mes"] = apontamento.data_apontamento.month
                        
                        grupos[key] = grupo
                    
                    # Atualizar horas e quantidade
                    if apontamento.horas_apontadas is not None:
                        grupos[key]["horas"] += float(apontamento.horas_apontadas)
                    grupos[key]["quantidade"] += 1
                    
                except Exception as e:
                    # Log do erro e continua
                    print(f"Erro ao processar apontamento {apontamento.id if hasattr(apontamento, 'id') else 'desconhecido'}: {str(e)}")
                    continue
            
            # Converter grupos para lista
            for grupo in grupos.values():
                resultado_agrupado.append(grupo)
            
            # Ordenar resultado
            if agrupar_por_recurso:
                resultado_agrupado.sort(key=lambda x: x.get("recurso_nome", "") if "recurso_nome" in x else x.get("recurso_id", 0))
            elif agrupar_por_projeto:
                resultado_agrupado.sort(key=lambda x: x.get("projeto_nome", "") if "projeto_nome" in x else x.get("projeto_id", 0))
            elif agrupar_por_mes:
                resultado_agrupado.sort(key=lambda x: (x.get("ano", 0), x.get("mes", 0)))
            
            return {
                "items": resultado_agrupado,
                "total": len(resultado_agrupado),
                "total_horas": sum(grupo["horas"] for grupo in resultado_agrupado)
            }
            
        except Exception as e:
            # Log do erro e lança exceção HTTP 500
            print(f"Erro ao processar relatório de horas apontadas: {str(e)}")
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"Erro ao processar relatório de horas apontadas: {str(e)}")