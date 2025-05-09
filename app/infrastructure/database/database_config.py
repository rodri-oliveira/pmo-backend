from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from typing import AsyncGenerator
from sqlalchemy.dialects.mssql import TINYINT

DATABASE_URL = settings.DATABASE_URI

# Crie engine e session síncronos
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Cria todas as tabelas no banco de dados
    Base.metadata.create_all(bind=engine)