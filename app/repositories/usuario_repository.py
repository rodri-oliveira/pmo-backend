from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.orm_models import Usuario
from app.repositories.base_repository import BaseRepository

class UsuarioRepository(BaseRepository[Usuario]):
    """Repositório para operações com a entidade Usuario."""
    
    def __init__(self, db: Session):
        super().__init__(db, Usuario)
    
    def get_by_email(self, email: str) -> Optional[Usuario]:
        """Obtém um usuário pelo email."""
        return self.db.query(Usuario).filter(Usuario.email == email).first()
    
    def update_last_access(self, id: int) -> None:
        """Atualiza o timestamp de último acesso do usuário."""
        user = self.get(id)
        if user:
            user.ultimo_acesso = datetime.utcnow()
            self.db.commit() 