from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator, Field

# Enums
class FonteApontamento(str, Enum):
    JIRA = "JIRA"
    MANUAL = "MANUAL"

class UserRole(str, Enum):
    ADMIN = "admin"
    GESTOR = "gestor"
    RECURSO = "recurso"

# Classes base
class BaseSchema(BaseModel):
    """Esquema base para todos os modelos Pydantic."""
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# Schemas para Secao
class SecaoBase(BaseSchema):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class SecaoCreate(SecaoBase):
    pass

class SecaoUpdate(BaseSchema):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None

class Secao(SecaoBase):
    id: int
    data_criacao: datetime
    data_atualizacao: datetime

# Schemas para Equipe
class EquipeBase(BaseSchema):
    secao_id: int
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class EquipeCreate(EquipeBase):
    pass

class EquipeUpdate(BaseSchema):
    secao_id: Optional[int] = None
    nome: Optional[str] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None

class Equipe(EquipeBase):
    id: int
    data_criacao: datetime
    data_atualizacao: datetime

# Schemas para Recurso
class RecursoBase(BaseSchema):
    nome: str
    email: EmailStr
    equipe_principal_id: Optional[int] = None
    matricula: Optional[str] = None
    cargo: Optional[str] = None
    jira_user_id: Optional[str] = None
    data_admissao: Optional[date] = None
    ativo: bool = True

class RecursoCreate(RecursoBase):
    pass

class RecursoUpdate(BaseSchema):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    equipe_principal_id: Optional[int] = None
    matricula: Optional[str] = None
    cargo: Optional[str] = None
    jira_user_id: Optional[str] = None
    data_admissao: Optional[date] = None
    ativo: Optional[bool] = None

class Recurso(RecursoBase):
    id: int
    data_criacao: datetime
    data_atualizacao: datetime

# Schemas para StatusProjeto
class StatusProjetoBase(BaseSchema):
    nome: str
    descricao: Optional[str] = None
    is_final: bool = False
    ordem_exibicao: Optional[int] = None

class StatusProjetoCreate(StatusProjetoBase):
    pass

class StatusProjetoUpdate(BaseSchema):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    is_final: Optional[bool] = None
    ordem_exibicao: Optional[int] = None

class StatusProjeto(StatusProjetoBase):
    id: int
    data_criacao: datetime
    data_atualizacao: datetime

# Schemas para Projeto
class ProjetoBase(BaseSchema):
    nome: str
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto: str
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    ativo: bool = True

class ProjetoCreate(ProjetoBase):
    pass

class ProjetoUpdate(BaseSchema):
    nome: Optional[str] = None
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto: Optional[str] = None
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    ativo: Optional[bool] = None

class Projeto(ProjetoBase):
    id: int
    data_criacao: datetime
    data_atualizacao: datetime

# Schemas para Apontamento
class ApontamentoBase(BaseSchema):
    recurso_id: int
    projeto_id: int
    jira_issue_key: Optional[str] = None
    data_hora_inicio_trabalho: Optional[datetime] = None
    data_apontamento: date
    horas_apontadas: Decimal
    descricao: Optional[str] = None

class ApontamentoCreate(ApontamentoBase):
    @validator('horas_apontadas')
    def validate_horas_apontadas(cls, v):
        if v <= 0 or v > 24:
            raise ValueError('Horas apontadas devem ser maiores que 0 e no máximo 24')
        return v

class ApontamentoUpdate(BaseSchema):
    recurso_id: Optional[int] = None
    projeto_id: Optional[int] = None
    jira_issue_key: Optional[str] = None
    data_hora_inicio_trabalho: Optional[datetime] = None
    data_apontamento: Optional[date] = None
    horas_apontadas: Optional[Decimal] = None
    descricao: Optional[str] = None
    
    @validator('horas_apontadas')
    def validate_horas_apontadas(cls, v):
        if v is not None and (v <= 0 or v > 24):
            raise ValueError('Horas apontadas devem ser maiores que 0 e no máximo 24')
        return v

class Apontamento(ApontamentoBase):
    id: int
    jira_worklog_id: Optional[str] = None
    fonte_apontamento: FonteApontamento
    id_usuario_admin_criador: Optional[int] = None
    data_sincronizacao_jira: Optional[datetime] = None
    data_criacao: datetime
    data_atualizacao: datetime

# Schemas para SincronizacaoJira
class SincronizacaoJiraBase(BaseSchema):
    data_inicio: datetime
    data_fim: Optional[datetime] = None
    status: str
    mensagem: Optional[str] = None
    quantidade_apontamentos_processados: Optional[int] = None
    usuario_id: Optional[int] = None

class SincronizacaoJiraOut(SincronizacaoJiraBase):
    id: int

# Esquemas para Planejado vs Realizado 2
from typing import Dict

class MesPlanejadoRealizado(BaseSchema):
    planejado: Optional[float] = None
    realizado: Optional[float] = None

# Schemas para Dashboard de Disponibilidade de Recursos

class ProjetoInfo(BaseSchema):
    id: int
    nome: str

class DisponibilidadeProjetoDetalhe(BaseModel):
    projeto: ProjetoInfo
    horas_planejadas: int

class DisponibilidadeMensal(BaseSchema):
    mes: int
    ano: int
    capacidade_rh: float
    total_horas_planejadas: float
    horas_livres: float
    percentual_alocacao: str
    alocacoes_detalhadas: List[DisponibilidadeProjetoDetalhe]

class RecursoInfo(BaseSchema):
    id: int
    nome: str

class DisponibilidadeRecursoResponse(BaseSchema):
    recurso: RecursoInfo
    disponibilidade_mensal: List[DisponibilidadeMensal]

class ProjetoPlanejadoRealizado(BaseSchema):
    id: int
    nome: str
    status: str
    alocacao_id: Optional[int] = None
    acao: Optional[str] = None
    esforco_estimado: Optional[float] = None
    esforco_planejado: Optional[float] = None
    meses: Dict[str, MesPlanejadoRealizado]

class LinhaResumo(BaseSchema):
    label: str
    esforco_planejado: float
    esforco_realizado: Optional[float] = None
    meses: Dict[str, MesPlanejadoRealizado]

class PlanejadoVsRealizadoResponse(BaseSchema):
    linhas_resumo: List[LinhaResumo]
    projetos: List[ProjetoPlanejadoRealizado]

class PlanejadoVsRealizadoRequest(BaseSchema):
    """Payload do endpoint Planejado vs Realizado 2.
    Somente recurso_id é obrigatório; demais filtros são opcionais.
    """
    recurso_id: int
    status_id: Optional[int] = None  # ID do status do projeto
    alocacao_id: Optional[int] = None  # Opcional: filtrar por alocação específica
    mes_inicio: Optional[str] = None  # YYYY-MM
    mes_fim: Optional[str] = None  # YYYY-MM

# Esquemas para agregações
class ApontamentoAgregado(BaseSchema):
    total_horas: Decimal
    total_registros: int
    recurso_id: Optional[int] = None
    projeto_id: Optional[int] = None
    data_apontamento: Optional[date] = None
    mes: Optional[int] = None
    ano: Optional[int] = None


# Schemas para o novo endpoint de disponibilidade por equipe
class AlocacaoMensalEquipe(BaseModel):
    mes: int
    percentual_alocacao: float

class RecursoAlocacaoEquipe(BaseModel):
    recurso_id: int
    recurso_nome: str
    alocacoes: List[AlocacaoMensalEquipe]

class DisponibilidadeEquipeResponse(BaseModel):
    equipe_id: int
    equipe_nome: str
    recursos: List[RecursoAlocacaoEquipe]


# Schemas para o novo endpoint de Análise de Alocação por Projeto
class KpisProjeto(BaseModel):
    total_recursos_envolvidos: int
    total_horas_planejadas: float
    media_alocacao_recursos_percentual: str

class AlocacaoMensalProjeto(BaseModel):
    mes: int
    ano: int
    total_horas_planejadas_no_projeto: float
    total_capacidade_recursos_envolvidos: float
    recursos_envolvidos_count: int

class DetalheRecursoProjeto(BaseModel):
    recurso_id: int
    recurso_nome: str
    total_horas_no_projeto: float
    percentual_do_total_projeto: str

class AlocacaoProjetoResponse(BaseModel):
    kpis_projeto: KpisProjeto
    alocacao_mensal: List[AlocacaoMensalProjeto]
    detalhe_recursos: List[DetalheRecursoProjeto]


# Schemas para o endpoint de Horas Disponíveis por Recurso
ANO_MES_REGEX = r"^\d{4}-(0[1-9]|1[0-2])$"

class HorasDisponiveisRequest(BaseModel):
    recurso_id: int
    data_inicio: str = Field(..., pattern=ANO_MES_REGEX, description="Mês de início no formato AAAA-MM")
    data_fim: str = Field(..., pattern=ANO_MES_REGEX, description="Mês de fim no formato AAAA-MM")

class MesHoras(BaseModel):
    mes: str # Formato AAAA-MM
    horas: float

class HorasDisponiveisResponse(BaseModel):
    recurso_id: int
    periodo: Dict[str, str]
    horas_por_mes: List[MesHoras]