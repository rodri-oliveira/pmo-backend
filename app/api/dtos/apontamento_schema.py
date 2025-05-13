from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import Field, field_validator

from .base_schema import BaseSchema, BaseResponseSchema


class FonteApontamento(str, Enum):
    """Enum para fonte de apontamento."""
    JIRA = "JIRA"
    MANUAL = "MANUAL"


class ApontamentoCreateSchema(BaseSchema):
    """Schema para criação de apontamento (sempre MANUAL pelo Admin)."""
    recurso_id: int
    projeto_id: int
    jira_issue_key: Optional[str] = Field(None, max_length=50)
    data_hora_inicio_trabalho: Optional[datetime] = None
    data_apontamento: date
    horas_apontadas: Decimal = Field(..., gt=0, le=24)
    descricao: Optional[str] = None
    
    @field_validator('horas_apontadas')
    @classmethod
    def validate_horas_apontadas(cls, v):
        """Valida que as horas apontadas estão entre 0 e 24."""
        if v <= 0 or v > 24:
            raise ValueError('Horas apontadas devem ser maiores que 0 e no máximo 24')
        return v


class ApontamentoUpdateSchema(BaseSchema):
    """Schema para atualização de apontamento (apenas para MANUAL)."""
    recurso_id: Optional[int] = None
    projeto_id: Optional[int] = None
    jira_issue_key: Optional[str] = Field(None, max_length=50)
    data_hora_inicio_trabalho: Optional[datetime] = None
    data_apontamento: Optional[date] = None
    horas_apontadas: Optional[Decimal] = Field(None, gt=0, le=24)
    descricao: Optional[str] = None
    
    @field_validator('horas_apontadas')
    @classmethod
    def validate_horas_apontadas(cls, v):
        """Valida que as horas apontadas estão entre 0 e 24."""
        if v is not None and (v <= 0 or v > 24):
            raise ValueError('Horas apontadas devem ser maiores que 0 e no máximo 24')
        return v


class ApontamentoResponseSchema(BaseResponseSchema):
    """Schema para resposta com dados de apontamento."""
    recurso_id: int
    projeto_id: int
    jira_issue_key: Optional[str] = None
    jira_worklog_id: Optional[str] = None
    data_hora_inicio_trabalho: Optional[datetime] = None
    data_apontamento: date
    horas_apontadas: Decimal
    descricao: Optional[str] = None
    fonte_apontamento: FonteApontamento
    id_usuario_admin_criador: Optional[int] = None
    data_sincronizacao_jira: Optional[datetime] = None


class ApontamentoFilterSchema(BaseSchema):
    """Schema para filtros de busca de apontamentos."""
    recurso_id: Optional[int] = None
    projeto_id: Optional[int] = None
    equipe_id: Optional[int] = None
    secao_id: Optional[int] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    fonte_apontamento: Optional[FonteApontamento] = None
    jira_issue_key: Optional[str] = None


class ApontamentoAggregationSchema(BaseResponseSchema):
    """Schema para agregações de apontamentos."""
    total_horas: Decimal
    total_registros: int
    recurso_id: Optional[int] = None
    projeto_id: Optional[int] = None
    data_apontamento: Optional[date] = None
    mes: Optional[int] = None
    ano: Optional[int] = None 