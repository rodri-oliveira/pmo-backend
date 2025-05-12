from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from fastapi import Depends

from app.core.config import settings

# Criar engine de conexão assíncrona com o PostgreSQL
async_engine = create_async_engine(
    settings.DATABASE_URI,
    echo=False, # Mantenha False para produção, True para debug de SQL
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
async def get_async_db() -> AsyncSession:
    """Dependency para injetar a sessão do banco assíncrona."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # O commit foi removido daqui. Ele deve ser feito nas operações de escrita do repositório.
        except Exception:
            await session.rollback() # Rollback em caso de exceção durante o uso da sessão
            raise
        # finally:
            # await session.close() # O async with AsyncSessionLocal() as session já cuida do fechamento.

# Para compatibilidade com código existente que pode estar usando get_db
get_db = get_async_db