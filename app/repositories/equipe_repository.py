from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.orm_models import Equipe
from app.repositories.base_repository import BaseRepository

class EquipeRepository(BaseRepository[Equipe]):
    """Repositório para operações com a entidade Equipe."""
    
    def __init__(self, db: Session):
        super().__init__(db, Equipe)
    
    def get_by_nome_and_secao(self, nome: str, secao_id: int) -> Optional[Equipe]:
        """Obtém uma equipe pelo nome e seção."""
        return self.db.query(Equipe).filter(
            Equipe.nome == nome,
            Equipe.secao_id == secao_id
        ).first()
    
    def list_by_secao(self, secao_id: int) -> List[Equipe]:
        """Lista equipes de uma seção."""
        return self.db.query(Equipe).filter(Equipe.secao_id == secao_id).all()
    
    def list(self, skip: int = 0, limit: int = 100, nome: Optional[str] = None, 
             secao_id: Optional[int] = None, ativo: Optional[bool] = None) -> List[Equipe]:
        """Lista equipes com filtros opcionais."""
        query = self.db.query(Equipe)
        
        if nome:
            query = query.filter(Equipe.nome.ilike(f"%{nome}%"))
        
        if secao_id:
            query = query.filter(Equipe.secao_id == secao_id)
        
        if ativo is not None:
            query = query.filter(Equipe.ativo == ativo)
        
        return query.offset(skip).limit(limit).all() 