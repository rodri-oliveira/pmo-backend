from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import relationship
from app.infrastructure.database.database_config import Base
from sqlalchemy import Column, DateTime

class RecursoSQL(Base):
    __tablename__ = "recurso"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    equipe_principal_id = Column(Integer, ForeignKey("equipe.id", ondelete="SET NULL"), nullable=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    matricula = Column(String(50), unique=True, nullable=True, index=True)
    cargo = Column(String(100), nullable=True)
    jira_user_id = Column(String(100), unique=True, nullable=True, index=True)
    data_admissao = Column(Date, nullable=True)
    data_criacao = Column(DateTime(timezone=True), nullable=False)
    data_atualizacao = Column(DateTime(timezone=True), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)

    equipe_principal = relationship("EquipeSQL") # Define relationship to EquipeSQL

