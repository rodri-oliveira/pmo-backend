from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends

from app.core.config import settings

# Criar engine de conexão com o PostgreSQL
engine = create_engine(settings.DATABASE_URI)

# Criar fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos ORM
Base = declarative_base()

# Dependency para obter sessão do banco
def get_db():
    """Dependency para injetar a sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 