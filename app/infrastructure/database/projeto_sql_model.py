from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import relationship
from app.infrastructure.database.database_config import Base
from sqlalchemy import Column, DateTime

class ProjetoSQL(Base):
    __tablename__ = "projeto"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(200), nullable=False)
    codigo_empresa = Column(String(50), unique=True, nullable=True, index=True)
    descricao = Column(Text, nullable=True)
    jira_project_key = Column(String(100), unique=True, nullable=True, index=True)
    status_projeto_id = Column(Integer, ForeignKey("status_projeto.id", ondelete="RESTRICT"), nullable=False, index=True)
    secao_id = Column(Integer, ForeignKey("secao.id", ondelete="RESTRICT"), nullable=True, index=True)
    data_inicio_prevista = Column(Date, nullable=True)
    data_fim_prevista = Column(Date, nullable=True)
    data_criacao = Column(DateTime(timezone=True), nullable=False)
    data_atualizacao = Column(DateTime(timezone=True), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)

    status_projeto = relationship("StatusProjetoSQL")
    secao = relationship("Secao")

