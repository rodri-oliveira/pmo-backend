from sqlalchemy import Column, Integer, SmallInteger, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database.database_config import Base

class HorasDisponiveisRhSQL(Base):
    __tablename__ = "horas_disponiveis_rh"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recurso_id = Column(Integer, ForeignKey("recurso.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False, index=True)
    ano = Column(SmallInteger, nullable=False, index=True)
    mes = Column(Integer, nullable=False, index=True)
    horas_disponiveis_mes = Column(Numeric(5,2), nullable=False)
    data_criacao = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    data_atualizacao = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    recurso = relationship("RecursoSQL")
