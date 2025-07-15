from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from typing import AsyncGenerator

DATABASE_URL = settings.DATABASE_URI

# 1. Crie um async_engine
async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log SQL queries
    future=True # Use a nova API do SQLAlchemy 2.0
)

# 2. Crie um AsyncSessionLocal (fábrica de sessões assíncronas)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Essencial para FastAPI
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# 3. Crie a dependência get_db assíncrona
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependência do FastAPI para obter uma sessão de banco de dados assíncrona.
    Garante que a sessão seja sempre fechada após a requisição.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """
    Inicializa o banco de dados, criando as tabelas se não existirem.
    """
    async with async_engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Descomente para apagar tudo ao iniciar
        await conn.run_sync(Base.metadata.create_all)