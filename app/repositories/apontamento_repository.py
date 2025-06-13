from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import func, extract, and_, or_, text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.db.orm_models import Apontamento, Recurso, Projeto, Equipe, Secao, FonteApontamento, equipe_projeto_association
from app.repositories.base_repository import BaseRepository
import logging
import calendar

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
        
        # Garantir que o campo jira_worklog_id seja salvo
        data["jira_worklog_id"] = jira_worklog_id
        
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
        aggregate: bool = False # Parâmetro mantido por compatibilidade de assinatura
    ) -> List[Dict[str, Any]]:
        """ 
        Busca e agrega os apontamentos com base em filtros dinâmicos, usando a lógica de consulta corrigida
        que realiza a agregação diretamente no banco de dados para garantir consistência e performance.
        """
        try:
            # Cláusulas de seleção e agrupamento dinâmicas
            select_clauses = [
                func.sum(Apontamento.horas_apontadas).label("horas"),
                func.count(Apontamento.id).label("qtd_lancamentos")
            ]
            group_by_clauses = []

            # Lógica de agrupamento dinâmico (define as colunas a serem selecionadas)
            if agrupar_por_recurso:
                select_clauses.extend([
                    Recurso.id.label("recurso_id"),
                    Recurso.nome.label("recurso_nome")
                ])
                group_by_clauses.extend([Recurso.id, Recurso.nome])

            if agrupar_por_projeto:
                select_clauses.extend([
                    Projeto.id.label("projeto_id"),
                    Projeto.nome.label("projeto_nome")
                ])
                group_by_clauses.extend([Projeto.id, Projeto.nome])

            if agrupar_por_data:
                select_clauses.append(Apontamento.data_apontamento.label("data"))
                group_by_clauses.append(Apontamento.data_apontamento)

            if agrupar_por_mes:
                # Usar date_trunc para agrupar por mês de forma robusta, evitando GroupingError no PostgreSQL
                month_trunc = func.date_trunc('month', Apontamento.data_apontamento)
                select_clauses.extend([
                    extract('year', month_trunc).label('ano'),
                    extract('month', month_trunc).label('mes'),
                    func.to_char(month_trunc, 'Month').label('mes_nome')
                ])
                # Agrupar pelo resultado da função date_trunc
                group_by_clauses.append(month_trunc)

            # Constrói a query base já com as colunas de seleção
            query = select(*select_clauses)

            # Adiciona os JOINs necessários
            query = query.select_from(Apontamento).join(Recurso, Apontamento.recurso_id == Recurso.id)
            query = query.join(Equipe, Recurso.equipe_principal_id == Equipe.id, isouter=True)
            query = query.join(Secao, Equipe.secao_id == Secao.id, isouter=True)

            if projeto_id or agrupar_por_projeto:
                query = query.join(Projeto, Apontamento.projeto_id == Projeto.id)

            # Filtros (cláusula WHERE)
            conditions = []
            if data_inicio:
                conditions.append(Apontamento.data_apontamento >= data_inicio)
            if data_fim:
                conditions.append(Apontamento.data_apontamento <= data_fim)
            if recurso_id:
                conditions.append(Apontamento.recurso_id == recurso_id)
            if projeto_id:
                conditions.append(Apontamento.projeto_id == projeto_id)
            if equipe_id:
                conditions.append(Recurso.equipe_principal_id == equipe_id)
            if secao_id:
                conditions.append(Equipe.secao_id == secao_id)
            if fonte_apontamento:
                conditions.append(Apontamento.fonte_apontamento == fonte_apontamento)
            if jira_issue_key:
                conditions.append(Apontamento.jira_issue_key == jira_issue_key)

            if conditions:
                query = query.where(and_(*conditions))
            
            # Adiciona o agrupamento
            if group_by_clauses:
                query = query.group_by(*group_by_clauses)

            # Executa a consulta
            result = await self.db.execute(query)
            return result.mappings().all()

            # Ajuste de tipos e nomenclatura para exibição
            month_names = {i: calendar.month_name[i] for i in range(1,13)}
            for grupo in resultado_agrupado:
                if "ano" in grupo:
                    grupo["ano"] = int(grupo["ano"])
                if "mes" in grupo:
                    mes_int = int(grupo["mes"])
                    grupo["mes"] = mes_int
                    grupo["mes_nome"] = month_names.get(mes_int)
                if "quantidade" in grupo:
                    grupo["qtd_lancamentos"] = int(grupo.pop("quantidade"))
                if "horas" in grupo:
                    grupo["horas"] = round(float(grupo["horas"]), 2)
            
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