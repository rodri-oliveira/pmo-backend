from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.orm_models import StatusProjeto
from app.repositories.base_repository import BaseRepository

class StatusProjetoRepository(BaseRepository[StatusProjeto]):
    """Repositório para operações com a entidade StatusProjeto."""
    
    def __init__(self, db: Session):
        super().__init__(db, StatusProjeto)
    
    def get_by_nome(self, nome: str) -> Optional[StatusProjeto]:
        """Obtém um status pelo nome."""
        return self.db.query(StatusProjeto).filter(StatusProjeto.nome == nome).first()
    
    def list_ordered_by_ordem(self) -> List[StatusProjeto]:
        """Lista status ordenados por ordem de exibição."""
        return self.db.query(StatusProjeto).order_by(StatusProjeto.ordem_exibicao).all()
    
    def get_final_status(self) -> List[StatusProjeto]:
        """Lista status que são finais (is_final=True)."""
        return self.db.query(StatusProjeto).filter(StatusProjeto.is_final == True).all() 