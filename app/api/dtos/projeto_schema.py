from datetime import date
from typing import Optional
from pydantic import Field

from .base_schema import BaseSchema, BaseResponseSchema


class ProjetoCreateSchema(BaseSchema):
    """Schema para criação de projeto."""
    nome: str = Field(..., min_length=1, max_length=200)
    codigo_empresa: Optional[str] = Field(None, max_length=50)
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = Field(None, max_length=100)
    status_projeto_id: int
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    ativo: bool = True


class ProjetoUpdateSchema(BaseSchema):
    """Schema para atualização de projeto."""
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    codigo_empresa: Optional[str] = Field(None, max_length=50)
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = Field(None, max_length=100)
    status_projeto_id: Optional[int] = None
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    ativo: Optional[bool] = None


class ProjetoResponseSchema(BaseResponseSchema):
    """Schema para resposta com dados de projeto."""
    nome: str
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto_id: int
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None 