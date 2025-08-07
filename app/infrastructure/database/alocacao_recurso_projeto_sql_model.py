from sqlalchemy import Column, Integer, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSRANGE
from sqlalchemy.sql import func
from app.infrastructure.database.database_config import Base

class AlocacaoRecursoProjetoSQL(Base):
    __tablename__ = "alocacao_recurso_projeto"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recurso_id = Column(Integer, ForeignKey("recurso.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False, index=True)
    projeto_id = Column(Integer, ForeignKey("projeto.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False, index=True)
    data_inicio_alocacao = Column(Date, nullable=False, index=True)
    data_fim_alocacao = Column(Date, nullable=True, index=True)
    periodo = Column(TSRANGE, nullable=True)
    equipe_id = Column(Integer, ForeignKey("equipe.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True, index=True)
    status_alocacao_id = Column(Integer, ForeignKey("status_projeto.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True, index=True)
    observacao = Column(Text, nullable=True)
    data_criacao = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    data_atualizacao = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    recurso = relationship("RecursoSQL")
    projeto = relationship("ProjetoSQL")
    equipe = relationship("EquipeSQL")
    status_alocacao = relationship("StatusProjetoSQL")

    # Relacionamento com horas planejadas - garante que o SQLAlchemy NÃO faça UPDATE
    # para NULL nos filhos durante a deleção da alocação. O banco (FK ON DELETE CASCADE)
    # cuidará da remoção.
    horas_planejadas = relationship(
        "HorasPlanejadasAlocacaoSQL",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="alocacao",
    )
