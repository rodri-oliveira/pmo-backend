from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from fastapi import Depends

from app.core.config import settings

# Criar engine de conexão assíncrona com o PostgreSQL
async_engine = create_async_engine(
    settings.DATABASE_URI,
    echo=False,
)

# Base para modelos ORM
Base = declarative_base()

# Criar fábrica de sessão assíncrona
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency para obter sessão do banco assíncrona
async def get_async_db():
    """Dependency para injetar a sessão do banco assíncrona."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.commit()

# Para compatibilidade com código existente
get_db = get_async_db