from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.database.database_config import Base

class UsuarioSQL(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    role = Column(Enum("ADMIN", "GESTOR", "RECURSO", name="role"), nullable=False)
    recurso_id = Column(Integer, ForeignKey("recurso.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True, index=True)
    data_criacao = Column(DateTime(timezone=True), nullable=False)
    data_atualizacao = Column(DateTime(timezone=True), nullable=False)
    ultimo_acesso = Column(DateTime(timezone=True), nullable=True)
    ativo = Column(Boolean, nullable=False)

    recurso = relationship("RecursoSQL")
