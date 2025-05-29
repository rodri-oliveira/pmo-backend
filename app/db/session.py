from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from fastapi import Depends

from app.core.config import settings

async_engine = create_async_engine(
    settings.DATABASE_URI,
    echo=False,  # Mantenha False para produção, True para debug de SQL
    pool_pre_ping=True,      # Garante que a conexão está viva antes de usar
    pool_recycle=1800,       # Recicla conexões antigas a cada 30 minutos
    pool_size=10,            # Número de conexões simultâneas (ajuste conforme necessário)
    max_overflow=20          # Número extra de conexões temporárias (ajuste conforme necessário)
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

# --- Sessão síncrona para endpoints legados ---
sync_engine = create_engine(
    settings.DATABASE_URI.replace('+asyncpg', ''),
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()