from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from app.infrastructure.database.database_config import Base
from sqlalchemy import Column, DateTime

class SecaoSQL(Base):
    __tablename__ = "secao"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False, unique=True)
    jira_project_key = Column(String(100), unique=True, nullable=True, index=True)
    descricao = Column(Text, nullable=True)
    data_criacao = Column(DateTime(timezone=True), nullable=False)
    data_atualizacao = Column(DateTime(timezone=True), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
