from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.orm_models import SincronizacaoJira

class SincronizacaoJiraRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: Dict[str, Any]) -> SincronizacaoJira:
        """Cria um registro de sincronização com o Jira"""
        sincronizacao = SincronizacaoJira(**data)
        self.db.add(sincronizacao)
        self.db.commit()
        self.db.refresh(sincronizacao)
        return sincronizacao
    
    def get_last_successful(self) -> Optional[SincronizacaoJira]:
        """Obtém a última sincronização bem-sucedida"""
        return self.db.query(SincronizacaoJira).filter(
            SincronizacaoJira.status == "SUCCESS"
        ).order_by(SincronizacaoJira.data_fim.desc()).first() 