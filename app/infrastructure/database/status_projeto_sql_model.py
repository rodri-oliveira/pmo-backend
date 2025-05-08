from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func, TinyInt
from app.infrastructure.database.database_config import Base

class StatusProjetoSQL(Base):
    __tablename__ = "status_projeto"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(50), nullable=False, unique=True)
    descricao = Column(String(255), nullable=True)
    is_final = Column(Boolean, nullable=False, default=False)
    ordem_exibicao = Column(TinyInt, unique=True, nullable=True) # Assuming TinyInt unsigned is handled by dialect or as Integer
    data_criacao = Column(DateTime, nullable=False, server_default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

