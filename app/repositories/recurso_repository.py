from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.orm_models import Recurso

class RecursoRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get(self, id: int) -> Optional[Recurso]:
        """Obtém um recurso pelo ID"""
        return self.db.query(Recurso).filter(Recurso.id == id).first()
    
    def get_by_jira_user_id(self, jira_user_id: str) -> Optional[Recurso]:
        """Obtém um recurso pelo ID de usuário do Jira"""
        return self.db.query(Recurso).filter(Recurso.jira_user_id == jira_user_id).first() 