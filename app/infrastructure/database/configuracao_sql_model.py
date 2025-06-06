from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.infrastructure.database.database_config import Base

class ConfiguracaoSQL(Base):
    __tablename__ = "configuracao"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chave = Column(String(100), unique=True, nullable=False, index=True)
    valor = Column(Text, nullable=True)
    descricao = Column(Text, nullable=True)
    data_criacao = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    data_atualizacao = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
