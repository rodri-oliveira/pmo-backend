from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from fastapi import Depends

# Use DATABASE_URI que já está configurado corretamente
DATABASE_URL = settings.DATABASE_URI

# Crie engine e session síncronos
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Função síncrona para fornecer a sessão do DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Inicialização síncrona do banco
def init_db():
    Base.metadata.create_all(bind=engine)

