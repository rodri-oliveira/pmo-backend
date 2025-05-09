from sqlalchemy import create_engine, SmallInteger  # Usar SmallInteger para PostgreSQL
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from typing import Generator

# Remover import do MySQL TINYINT
# from sqlalchemy.dialects.mysql import TINYINT

DATABASE_URL = settings.DATABASE_URI

# Crie engine e session síncronos
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Cria todas as tabelas no banco de dados
    Base.metadata.create_all(bind=engine)