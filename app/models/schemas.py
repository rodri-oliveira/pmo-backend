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
        orm_mode = True
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
    status_projeto_id: int
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
    status_projeto_id: Optional[int] = None
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

# Esquemas para agregações
class ApontamentoAgregado(BaseSchema):
    total_horas: Decimal
    total_registros: int
    recurso_id: Optional[int] = None
    projeto_id: Optional[int] = None
    data_apontamento: Optional[date] = None
    mes: Optional[int] = None
    ano: Optional[int] = None 