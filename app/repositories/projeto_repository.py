from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.orm_models import Projeto
from app.repositories.base_repository import BaseRepository

class ProjetoRepository(BaseRepository[Projeto, int]):
    """Repositório para operações com a entidade Projeto."""
    
    def __init__(self, db: Session):
        super().__init__(db, Projeto)
    
    def get_by_codigo_empresa(self, codigo_empresa: str) -> Optional[Projeto]:
        """Obtém um projeto pelo código da empresa."""
        return self.db.query(Projeto).filter(Projeto.codigo_empresa == codigo_empresa).first()
    
    def get_by_jira_project_key(self, jira_project_key: str) -> Optional[Projeto]:
        """Obtém um projeto pela chave do projeto no Jira."""
        return self.db.query(Projeto).filter(Projeto.jira_project_key == jira_project_key).first()
    
    def list_by_status(self, status_id: int) -> List[Projeto]:
        """Lista projetos com um determinado status."""
        return self.db.query(Projeto).filter(Projeto.status_projeto_id == status_id).all()
    
    def list(self, skip: int = 0, limit: int = 100, nome: Optional[str] = None, 
             status_id: Optional[int] = None, ativo: Optional[bool] = None) -> List[Projeto]:
        """Lista projetos com filtros opcionais."""
        query = self.db.query(Projeto)
        
        if nome:
            query = query.filter(Projeto.nome.ilike(f"%{nome}%"))
        
        if status_id:
            query = query.filter(Projeto.status_projeto_id == status_id)
        
        if ativo is not None:
            query = query.filter(Projeto.ativo == ativo)
        
        return query.offset(skip).limit(limit).all() 