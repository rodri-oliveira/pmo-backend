from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.orm_models import Usuario
from app.repositories.base_repository import BaseRepository

class UsuarioRepository(BaseRepository[Usuario]):
    """Repositório para operações com a entidade Usuario."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Usuario)
    
    async def get_by_email(self, email: str) -> Optional[Usuario]:
        """Obtém um usuário pelo email."""
        result = await self.db.execute(select(Usuario).filter(Usuario.email == email))
        return result.scalars().first()
    
    async def get_by_username(self, username: str) -> Optional[Usuario]:
        """Obtém um usuário pelo username (email)."""
        result = await self.db.execute(select(Usuario).filter(Usuario.email == username))
        return result.scalars().first()
    
    async def update_last_access(self, id: int) -> None:
        """Atualiza o timestamp de último acesso do usuário."""
        user = await self.get(id)
        if user:
            user.ultimo_acesso = datetime.now(timezone.utc)
            await self.db.commit()