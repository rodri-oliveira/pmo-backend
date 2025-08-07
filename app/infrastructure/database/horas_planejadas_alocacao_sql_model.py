from sqlalchemy import Column, Integer, SmallInteger, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database.database_config import Base

class HorasPlanejadasAlocacaoSQL(Base):
    __tablename__ = "horas_planejadas_alocacao"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alocacao_id = Column(Integer, ForeignKey("alocacao_recurso_projeto.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False, index=True)
    ano = Column(SmallInteger, nullable=False, index=True)
    mes = Column(Integer, nullable=False, index=True)
    horas_planejadas = Column(Numeric(5,2), nullable=False)
    data_criacao = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    data_atualizacao = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Use passive_deletes to let the database handle cascade deletion and
    # prevent SQLAlchemy from issuing an UPDATE that sets alocacao_id to NULL
    # (which violates the NOT NULL constraint).
    alocacao = relationship(
        "AlocacaoRecursoProjetoSQL",
        passive_deletes=True,
        back_populates="horas_planejadas",
    )
