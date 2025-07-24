from sqlalchemy import Column, Integer, String, Text, Date, DateTime, DECIMAL, Enum, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import relationship
from app.infrastructure.database.database_config import Base


class ApontamentoSQL(Base):
    __tablename__ = "apontamento"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    jira_worklog_id = Column(String(255), unique=True, nullable=True)
    recurso_id = Column(Integer, ForeignKey("recurso.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False, index=True)
    projeto_id = Column(Integer, ForeignKey("projeto.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False, index=True)
    jira_issue_key = Column(String(50), nullable=True)
    jira_parent_key = Column(String(50), nullable=True, index=True)
    jira_issue_type = Column(String(50), nullable=True, index=True)
    nome_subtarefa = Column(String(200), nullable=True)
    projeto_pai_id = Column(Integer, ForeignKey("projeto.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True, index=True)
    nome_projeto_pai = Column(String(200), nullable=True)
    data_hora_inicio_trabalho = Column(DateTime(timezone=True), nullable=True)
    data_apontamento = Column(Date, nullable=False, index=True)
    horas_apontadas = Column(DECIMAL(5, 2), nullable=False)
    descricao = Column(Text, nullable=True)
    fonte_apontamento = Column(Enum("JIRA", "MANUAL", name="fonteapontamento"), nullable=False)
    id_usuario_admin_criador = Column(Integer, ForeignKey("usuario.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True, index=True)
    data_sincronizacao_jira = Column(DateTime(timezone=True), nullable=True)
    data_criacao = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    data_atualizacao = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    recurso = relationship("RecursoSQL")
    projeto = relationship("ProjetoSQL", foreign_keys=[projeto_id])
    projeto_pai = relationship("ProjetoSQL", foreign_keys=[projeto_pai_id])
    usuario_admin = relationship("UsuarioSQL", foreign_keys=[id_usuario_admin_criador])

    __table_args__ = (
        CheckConstraint("horas_apontadas > 0 AND horas_apontadas <= 24", name="chk_apontamento_horas"),
    )
