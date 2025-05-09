from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.infrastructure.database.database_config import Base

class EquipeSQL(Base):
    __tablename__ = "equipe"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    secao_id = Column(Integer, ForeignKey("secao.id"), nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    data_criacao = Column(DateTime, nullable=False, server_default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    ativo = Column(Boolean, nullable=False, default=True)

    secao = relationship("SecaoSQL") # Define relationship to SecaoSQL if needed for ORM queries

