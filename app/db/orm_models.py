from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, Float, ForeignKey, Enum, UniqueConstraint, CheckConstraint, DECIMAL, SmallInteger, TIMESTAMP, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.db.session import Base

# Associação N:N equipe_projeto
equipe_projeto_association = Table(
    "equipe_projeto",
    Base.metadata,
    Column("equipe_id", Integer, ForeignKey("equipe.id", ondelete="CASCADE"), primary_key=True),
    Column("projeto_id", Integer, ForeignKey("projeto.id", ondelete="CASCADE"), primary_key=True),
)

# Enum para fonte de apontamento
class FonteApontamento(str, PyEnum):
    JIRA = "JIRA"
    MANUAL = "MANUAL"

# Enum para roles de usuário
class UserRole(str, PyEnum):
    ADMIN = "admin"
    GESTOR = "gestor"
    RECURSO = "recurso"

# Modelos ORM baseados no esquema do BD v1.2

class Secao(Base):
    __tablename__ = "secao"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False, unique=True)
    descricao = Column(Text, nullable=True)
    jira_project_key = Column(String(20), nullable=True, unique=True, index=True)  # Chave do Jira para vinculação
    data_criacao = Column(DateTime, nullable=False, default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    ativo = Column(Boolean, nullable=False, default=True)
    
    # Relacionamentos
    equipes = relationship("Equipe", back_populates="secao")

class Equipe(Base):
    __tablename__ = "equipe"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    secao_id = Column(Integer, ForeignKey("secao.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    data_criacao = Column(DateTime, nullable=False, default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    ativo = Column(Boolean, nullable=False, default=True)
    
    # Relacionamentos
    secao = relationship("Secao", back_populates="equipes")
    recursos = relationship("Recurso", back_populates="equipe_principal")
    # Associação N:N com projetos
    projetos = relationship(
        "Projeto",
        secondary=equipe_projeto_association,
        back_populates="equipes"
    )
    
    # Restrições
    __table_args__ = (
        UniqueConstraint('secao_id', 'nome', name='uq_equipe_secao_nome'),
    )

class Recurso(Base):
    __tablename__ = "recurso"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    equipe_principal_id = Column(Integer, ForeignKey("equipe.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    matricula = Column(String(50), nullable=True, unique=True, index=True)
    cargo = Column(String(100), nullable=True)
    jira_user_id = Column(String(100), nullable=True, unique=True, index=True)
    data_admissao = Column(Date, nullable=True)
    data_criacao = Column(DateTime, nullable=False, default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    ativo = Column(Boolean, nullable=False, default=True)
    
    # Relacionamentos
    equipe_principal = relationship("Equipe", back_populates="recursos")
    usuario = relationship("Usuario", back_populates="recurso", uselist=False)
    alocacoes = relationship("AlocacaoRecursoProjeto", back_populates="recurso")
    horas_disponiveis = relationship("HorasDisponiveisRH", back_populates="recurso")
    apontamentos = relationship("Apontamento", back_populates="recurso")

class StatusProjeto(Base):
    __tablename__ = "status_projeto"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False, unique=True)
    descricao = Column(String(255), nullable=True)
    is_final = Column(Boolean, nullable=False, default=False)
    ordem_exibicao = Column(Integer, nullable=True, unique=True)
    data_criacao = Column(DateTime, nullable=False, default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    projetos = relationship("Projeto", back_populates="status")

class Projeto(Base):
    __tablename__ = "projeto"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200), nullable=False)
    codigo_empresa = Column(String(50), nullable=True, unique=True, index=True)
    descricao = Column(Text, nullable=True)
    jira_project_key = Column(String(100), nullable=True, index=True)  # unique=False para permitir múltiplos projetos com a mesma key
    status_projeto_id = Column(Integer, ForeignKey("status_projeto.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    secao_id = Column(Integer, ForeignKey("secao.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=True, index=True)
    data_inicio_prevista = Column(Date, nullable=True)
    data_fim_prevista = Column(Date, nullable=True)
    data_criacao = Column(DateTime, nullable=False, default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    ativo = Column(Boolean, nullable=False, default=True)
    
    # Relacionamentos
    status = relationship("StatusProjeto", back_populates="projetos")
    secao = relationship("Secao")
    alocacoes = relationship("AlocacaoRecursoProjeto", back_populates="projeto")
    apontamentos = relationship("Apontamento", back_populates="projeto")
    # Associação N:N com equipes
    equipes = relationship(
        "Equipe",
        secondary=equipe_projeto_association,
        back_populates="projetos"
    )

class AlocacaoRecursoProjeto(Base):
    __tablename__ = "alocacao_recurso_projeto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recurso_id = Column(Integer, ForeignKey("recurso.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    projeto_id = Column(Integer, ForeignKey("projeto.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    equipe_id = Column(Integer, ForeignKey("equipe.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    status_alocacao_id = Column(Integer, ForeignKey("status_projeto.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    observacao = Column(Text, nullable=True)
    data_inicio_alocacao = Column(Date, nullable=False)
    data_fim_alocacao = Column(Date, nullable=True)
    data_criacao = Column(DateTime, nullable=False, default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    esforco_estimado = Column(DECIMAL(10, 2), nullable=True)
    esforco_planejado = Column(DECIMAL(10, 2), nullable=True)

    # Relacionamentos
    recurso = relationship("Recurso", back_populates="alocacoes")
    projeto = relationship("Projeto", back_populates="alocacoes")
    equipe = relationship("Equipe")
    status_alocacao = relationship("StatusProjeto")
    horas_planejadas = relationship("HorasPlanejadas", back_populates="alocacao")
    
    # Restrições
    __table_args__ = (
        UniqueConstraint('recurso_id', 'projeto_id', 'data_inicio_alocacao', name='uq_alocacao_recurso_projeto_data'),
        CheckConstraint('data_fim_alocacao IS NULL OR data_fim_alocacao >= data_inicio_alocacao', name='chk_alocacao_datas'),
    )

class HorasDisponiveisRH(Base):
    __tablename__ = "horas_disponiveis_rh"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    recurso_id = Column(Integer, ForeignKey("recurso.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    ano = Column(SmallInteger, nullable=False)
    mes = Column(Integer, nullable=False)
    horas_disponiveis_mes = Column(DECIMAL(5, 2), nullable=False)
    data_criacao = Column(DateTime, nullable=False, default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    recurso = relationship("Recurso", back_populates="horas_disponiveis")
    
    # Restrições
    __table_args__ = (
        UniqueConstraint('recurso_id', 'ano', 'mes', name='uq_horas_disponveis_recurso_ano_mes'),
        CheckConstraint('mes >= 1 AND mes <= 12', name='chk_horas_disponveis_mes'),
        CheckConstraint('horas_disponiveis_mes >= 0', name='chk_horas_disponveis_valor'),
    )

class HorasPlanejadas(Base):
    __tablename__ = "horas_planejadas_alocacao"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alocacao_id = Column(Integer, ForeignKey("alocacao_recurso_projeto.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    ano = Column(SmallInteger, nullable=False)
    mes = Column(Integer, nullable=False)
    horas_planejadas = Column(DECIMAL(5, 2), nullable=False)
    data_criacao = Column(DateTime, nullable=False, default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    alocacao = relationship("AlocacaoRecursoProjeto", back_populates="horas_planejadas")
    
    # Restrições
    __table_args__ = (
        UniqueConstraint('alocacao_id', 'ano', 'mes', name='uq_horas_planejadas_alocacao_ano_mes'),
        CheckConstraint('mes >= 1 AND mes <= 12', name='chk_horas_planejadas_mes'),
        CheckConstraint('horas_planejadas >= 0', name='chk_horas_planejadas_valor'),
    )

class Apontamento(Base):
    __tablename__ = "apontamento"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    jira_worklog_id = Column(String(255), nullable=True, unique=True, index=True)
    recurso_id = Column(Integer, ForeignKey("recurso.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    projeto_id = Column(Integer, ForeignKey("projeto.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    jira_issue_key = Column(String(50), nullable=True, index=True)
    data_hora_inicio_trabalho = Column(DateTime, nullable=True)
    data_apontamento = Column(Date, nullable=False, index=True)
    horas_apontadas = Column(DECIMAL(5, 2), nullable=False)
    descricao = Column(Text, nullable=True)
    fonte_apontamento = Column(Enum(FonteApontamento), nullable=False, default=FonteApontamento.MANUAL, index=True)
    id_usuario_admin_criador = Column(Integer, ForeignKey("usuario.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    data_sincronizacao_jira = Column(DateTime, nullable=True)
    data_criacao = Column(DateTime, nullable=False, default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    recurso = relationship("Recurso", back_populates="apontamentos")
    projeto = relationship("Projeto", back_populates="apontamentos")
    usuario_criador = relationship("Usuario", back_populates="apontamentos_criados")
    
    # Restrições
    __table_args__ = (
        CheckConstraint('horas_apontadas > 0 AND horas_apontadas <= 24', name='chk_apontamento_horas'),
    )

class Usuario(Base):
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    senha_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    recurso_id = Column(Integer, ForeignKey("recurso.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, unique=True)
    data_criacao = Column(DateTime, nullable=False, default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    ultimo_acesso = Column(DateTime, nullable=True)
    ativo = Column(Boolean, nullable=False, default=True)
    
    # Relacionamentos
    recurso = relationship("Recurso", back_populates="usuario")
    apontamentos_criados = relationship("Apontamento", back_populates="usuario_criador")
    logs = relationship("LogAtividade", back_populates="usuario")
    sincronizacoes = relationship("SincronizacaoJira", back_populates="usuario")

class Configuracao(Base):
    __tablename__ = "configuracao"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chave = Column(String(100), nullable=False, unique=True)
    valor = Column(Text, nullable=True)
    descricao = Column(Text, nullable=True)
    data_criacao = Column(DateTime, nullable=False, default=func.now())
    data_atualizacao = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

class LogAtividade(Base):
    __tablename__ = "log_atividade"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    acao = Column(String(255), nullable=False)
    tabela_afetada = Column(String(100), nullable=True)
    registro_id = Column(String(255), nullable=True)
    detalhes = Column(Text, nullable=True)
    ip_origem = Column(String(45), nullable=True)
    data_hora = Column(TIMESTAMP(6), nullable=False, default=func.now(), index=True)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="logs")

class SincronizacaoJira(Base):
    __tablename__ = "sincronizacao_jira"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    data_inicio = Column(DateTime, nullable=False)
    data_fim = Column(DateTime, nullable=True)  # Pode ser NULL durante o processamento
    status = Column(String(50), nullable=False)
    mensagem = Column(Text, nullable=True)
    quantidade_apontamentos_processados = Column(Integer, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="sincronizacoes")

class DimTempo(Base):
    __tablename__ = "dim_tempo"
    
    data_id = Column(Integer, primary_key=True)
    data = Column(Date, nullable=False, unique=True)
    ano = Column(SmallInteger, nullable=False)
    mes = Column(Integer, nullable=False)
    dia = Column(Integer, nullable=False)
    trimestre = Column(Integer, nullable=False)
    dia_semana = Column(Integer, nullable=False)
    nome_dia_semana = Column(String(20), nullable=False)
    nome_mes = Column(String(20), nullable=False)
    semana_ano = Column(Integer, nullable=False)
    is_dia_util = Column(Boolean, nullable=False)
    is_feriado = Column(Boolean, nullable=False, default=False)
    nome_feriado = Column(String(100), nullable=True) 