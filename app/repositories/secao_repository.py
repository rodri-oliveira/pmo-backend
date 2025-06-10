from app.db.orm_models import Secao
from app.repositories.base_repository import BaseRepository
from typing import Optional
from sqlalchemy import select

class SecaoRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Secao)

    def get(self, id):
        return self.db.query(Secao).filter(Secao.id == id).first()

    def list(self):
        return self.db.query(Secao).all()
    
    async def get_by_jira_project_key(self, jira_project_key: str) -> Optional[Secao]:
        """
        Busca uma secao pelo jira_project_key.
        """
        query = select(self.model).where(self.model.jira_project_key == jira_project_key)
        result = await self.db.execute(query)
        return result.scalars().first()
