from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database.database_config import Base

class SincronizacaoJiraSQL(Base):
    __tablename__ = "sincronizacao_jira"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    data_inicio = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    data_fim = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False)
    mensagem = Column(Text, nullable=True)
    quantidade_apontamentos_processados = Column(Integer, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True, index=True)

    usuario = relationship("UsuarioSQL")
