from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database.database_config import Base

class LogAtividadeSQL(Base):
    __tablename__ = "log_atividade"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True, index=True)
    acao = Column(String(255), nullable=False)
    tabela_afetada = Column(String(100), nullable=True)
    registro_id = Column(String(255), nullable=True)
    detalhes = Column(Text, nullable=True)
    ip_origem = Column(String(45), nullable=True)
    data_hora = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    usuario = relationship("UsuarioSQL")
