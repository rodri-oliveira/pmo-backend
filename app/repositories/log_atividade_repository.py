from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.orm_models import LogAtividade
from app.repositories.base_repository import BaseRepository

class LogAtividadeRepository(BaseRepository[LogAtividade]):
    """
    Repositório para operações com logs de atividade do sistema.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o repositório com uma sessão do banco de dados.
        
        Args:
            db: Sessão do banco de dados
        """
        super().__init__(db, LogAtividade)
    
    def log_action(
        self, 
        acao: str, 
        entidade: str, 
        entidade_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
        detalhes: Optional[str] = None
    ) -> LogAtividade:
        """
        Registra uma ação no sistema.
        
        Args:
            acao: Tipo de ação (criar, atualizar, excluir)
            entidade: Nome da entidade afetada
            entidade_id: ID da entidade afetada
            usuario_id: ID do usuário que realizou a ação
            detalhes: Detalhes adicionais
            
        Returns:
            Registro de log criado
        """
        return self.create({
            "acao": acao,
            "entidade": entidade,
            "entidade_id": entidade_id,
            "usuario_id": usuario_id,
            "detalhes": detalhes,
            "data_hora": datetime.now()
        })
    
    def get_logs_by_entity(self, entidade: str, entidade_id: Optional[int] = None) -> List[LogAtividade]:
        """
        Obtém logs relacionados a uma entidade específica.
        
        Args:
            entidade: Nome da entidade
            entidade_id: ID da entidade
            
        Returns:
            Lista de logs
        """
        query = self.db.query(self.model).filter(self.model.entidade == entidade)
        
        if entidade_id is not None:
            query = query.filter(self.model.entidade_id == entidade_id)
            
        return query.order_by(self.model.data_hora.desc()).all()
    
    def get_logs_by_user(self, usuario_id: int) -> List[LogAtividade]:
        """
        Obtém logs de ações realizadas por um usuário específico.
        
        Args:
            usuario_id: ID do usuário
            
        Returns:
            Lista de logs
        """
        return self.db.query(self.model).filter(
            self.model.usuario_id == usuario_id
        ).order_by(
            self.model.data_hora.desc()
        ).all() 