from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging
from fastapi.encoders import jsonable_encoder

logging.basicConfig(level=logging.INFO)
from datetime import datetime

from app.db.orm_models import SincronizacaoJira
from app.repositories.base_repository import BaseRepository

class SincronizacaoJiraRepository(BaseRepository[SincronizacaoJira]):
    """
    Repositório para operações com registros de sincronização do Jira.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa o repositório com uma sessão do banco de dados.
        
        Args:
            db: Sessão do banco de dados assíncrona
        """
        super().__init__(db, SincronizacaoJira)
    
    def create_sync_record(self, tipo_evento: str, payload: str, status: str = "RECEBIDO") -> SincronizacaoJira:
        """
        Cria um registro de sincronização.
        
        Args:
            tipo_evento: Tipo de evento (worklog_created, worklog_updated, worklog_deleted)
            payload: Payload do webhook em formato JSON string
            status: Status da sincronização
            
        Returns:
            Registro de sincronização criado
        """
        return self.create({
            "tipo_evento": tipo_evento,
            "payload": payload,
            "status": status,
            "data_hora": datetime.now()
        })
    
    def update_sync_status(self, id: int, status: str, detalhes: Optional[str] = None) -> Optional[SincronizacaoJira]:
        """
        Atualiza o status de uma sincronização.
        
        Args:
            id: ID do registro de sincronização
            status: Novo status
            detalhes: Detalhes adicionais
            
        Returns:
            Registro atualizado ou None se não encontrado
        """
        update_data = {"status": status}
        if detalhes:
            update_data["detalhes"] = detalhes
            
        return self.update(id, update_data)
    
    async def list_with_pagination(self, skip: int = 0, limit: int = 50, status: Optional[str] = None, tipo_evento: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lista sincronizações com paginação e filtros opcionais.
        Args:
            skip: Quantidade de registros a pular
            limit: Quantidade máxima de registros
            status: Filtro por status
            tipo_evento: Filtro por tipo de evento
        Returns:
            (Lista de registros serializados, total de registros)
        """
        logging.info(f"[SINCRONIZACAO_JIRA_REPO] Listando sincronizações com skip={skip}, limit={limit}, status={status}, tipo_evento={tipo_evento}")
        logging.info(f"[SINCRONIZACAO_JIRA_REPO] Tipo de sessão DB: {type(self.db)}")
        
        try:
            # Construir a consulta usando a API de consulta do SQLAlchemy 2.0
            query = select(self.model)
            
            # Adicionar filtros se fornecidos
            if status:
                query = query.where(self.model.status == status)
            if tipo_evento:
                query = query.where(self.model.tipo_evento == tipo_evento)
            
            # Contar o total de registros
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0
            
            # Obter os itens com ordenação, offset e limit
            query = query.order_by(self.model.data_inicio.desc()).offset(skip).limit(limit)
            result = await self.db.execute(query)
            items_db = result.scalars().all()
            
            # Serializar os objetos para dicionários
            items = []
            for item in items_db:
                # Converter datetime para string para facilitar a serialização JSON
                item_dict = {
                    "id": item.id,
                    "data_inicio": item.data_inicio.isoformat() if item.data_inicio else None,
                    "data_fim": item.data_fim.isoformat() if item.data_fim else None,
                    "status": item.status,
                    "mensagem": item.mensagem,
                    "quantidade_apontamentos_processados": item.quantidade_apontamentos_processados,
                    "usuario_id": item.usuario_id
                }
                items.append(item_dict)
            
            logging.info(f"[SINCRONIZACAO_JIRA_REPO] Encontrados {total} registros")
            return items, total
        except Exception as e:
            logging.error(f"[SINCRONIZACAO_JIRA_REPO] Erro ao listar sincronizações: {str(e)}")
            # Retornar lista vazia em caso de erro
            return [], 0

    async def create(self, obj_in: Dict[str, Any]) -> SincronizacaoJira:
        """
        Cria um novo registro de sincronização.
        
        Args:
            obj_in: Dados para criar o registro
            
        Returns:
            Registro criado
        """
        import logging
        logging.info(f"[SINCRONIZACAO_JIRA_REPO] Criando registro de sincronização: {obj_in}")
        
        try:
            # Não usar jsonable_encoder para evitar conversão de datetime para string
            # Criar diretamente o objeto com os dados originais
            db_obj = self.model(
                data_inicio=obj_in["data_inicio"],
                data_fim=obj_in["data_fim"],
                status=obj_in["status"],
                mensagem=obj_in["mensagem"],
                quantidade_apontamentos_processados=obj_in["quantidade_apontamentos_processados"]
                # Não incluir usuario_id se não estiver presente
            )
            
            # Adicionar usuario_id apenas se estiver presente no dicionário
            if "usuario_id" in obj_in and obj_in["usuario_id"] is not None:
                db_obj.usuario_id = obj_in["usuario_id"]
                
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            logging.info(f"[SINCRONIZACAO_JIRA_REPO] Registro criado com ID: {db_obj.id}")
            return db_obj
        except Exception as e:
            await self.db.rollback()
            logging.error(f"[SINCRONIZACAO_JIRA_REPO] Erro ao criar registro: {str(e)}")
            raise

    async def get_recent_syncs(self, limit: int = 50) -> List[SincronizacaoJira]:
        """
        Obtém as sincronizações mais recentes.
        
        Args:
            limit: Número máximo de registros
            
        Returns:
            Lista de registros de sincronização
        """
        query = select(self.model).order_by(self.model.data_inicio.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_failed_syncs(self) -> List[SincronizacaoJira]:
        """
        Obtém sincronizações que falharam.
        
        Returns:
            Lista de registros de sincronização com falha
        """
        query = select(self.model).where(self.model.status == "ERRO").order_by(self.model.data_inicio.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_last_successful(self) -> Optional[SincronizacaoJira]:
        """Obtém a última sincronização bem-sucedida"""
        query = select(self.model).where(self.model.status == "SUCESSO").order_by(self.model.data_fim.desc()).limit(1)
        result = await self.db.execute(query)
        return result.scalars().first()