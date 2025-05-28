from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.orm_models import SincronizacaoJira
from app.repositories.base_repository import BaseRepository

class SincronizacaoJiraRepository(BaseRepository[SincronizacaoJira]):
    """
    Repositório para operações com registros de sincronização do Jira.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o repositório com uma sessão do banco de dados.
        
        Args:
            db: Sessão do banco de dados
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
    
    def list_with_pagination(self, skip: int = 0, limit: int = 50, status: Optional[str] = None, tipo_evento: Optional[str] = None) -> (List[SincronizacaoJira], int):
        """
        Lista sincronizações com paginação e filtros opcionais.
        Args:
            skip: Quantidade de registros a pular
            limit: Quantidade máxima de registros
            status: Filtro por status
            tipo_evento: Filtro por tipo de evento
        Returns:
            (Lista de registros, total de registros)
        """
        query = self.db.query(self.model)
        if status:
            query = query.filter(self.model.status == status)
        if tipo_evento:
            query = query.filter(self.model.tipo_evento == tipo_evento)
        total = query.count()
        items = query.order_by(self.model.data_hora.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_recent_syncs(self, limit: int = 50) -> List[SincronizacaoJira]:
        """
        Obtém as sincronizações mais recentes.
        
        Args:
            limit: Número máximo de registros
            
        Returns:
            Lista de registros de sincronização
        """
        return self.db.query(self.model).order_by(
            self.model.data_hora.desc()
        ).limit(limit).all()
    
    def get_failed_syncs(self) -> List[SincronizacaoJira]:
        """
        Obtém sincronizações que falharam.
        
        Returns:
            Lista de registros de sincronização com falha
        """
        return self.db.query(self.model).filter(
            self.model.status == "ERRO"
        ).order_by(
            self.model.data_hora.desc()
        ).all()

    def get_last_successful(self) -> Optional[SincronizacaoJira]:
        """Obtém a última sincronização bem-sucedida"""
        return self.db.query(SincronizacaoJira).filter(
            SincronizacaoJira.status == "SUCCESS"
        ).order_by(SincronizacaoJira.data_fim.desc()).first() 