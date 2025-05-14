from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func, SmallInteger
from app.infrastructure.database.database_config import Base
from sqlalchemy import Column, DateTime

class StatusProjetoSQL(Base):
    __tablename__ = "status_projeto"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(50), nullable=False, unique=True)
    descricao = Column(String(255), nullable=True)
    is_final = Column(Boolean, nullable=False, default=False)
    ordem_exibicao = Column(SmallInteger, unique=True, nullable=True)  # Usando SmallInteger em vez de TinyInt
    data_criacao = Column(DateTime(timezone=True), nullable=False)
    data_atualizacao = Column(DateTime(timezone=True), nullable=False)

