from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from app.infrastructure.database.database_config import Base

class SecaoSQL(Base):
    __tablename__ = "secao"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False, unique=True)
    descricao = Column(Text, nullable=True)
    data_criacao = Column(DateTime, nullable=False, server_default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    ativo = Column(Boolean, nullable=False, default=True)

