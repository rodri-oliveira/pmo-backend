from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from fastapi import Depends

from app.core.config import settings

# Criar engine de conexão assíncrona com o PostgreSQL
async_engine = create_async_engine(
    settings.DATABASE_URI,
    echo=False,
    future=True,
    # Estas configurações são importantes para resolver o erro MissingGreenlet
    pool_pre_ping=True,
    pool_use_lifo=True,
)

# Criar fábrica de sessões assíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base para modelos ORM
Base = declarative_base()

# Dependency para obter sessão do banco assíncrona
async def get_async_db():
    """Dependency para injetar a sessão do banco assíncrona."""
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

# Para compatibilidade com código existente
get_db = get_async_db