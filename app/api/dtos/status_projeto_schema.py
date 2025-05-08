from typing import Optional
from pydantic import Field

from .base_schema import BaseSchema, BaseResponseSchema


class StatusProjetoCreateSchema(BaseSchema):
    """Schema para criação de status de projeto."""
    nome: str = Field(..., min_length=1, max_length=50)
    descricao: Optional[str] = Field(None, max_length=255)
    is_final: bool = False
    ordem_exibicao: Optional[int] = None


class StatusProjetoUpdateSchema(BaseSchema):
    """Schema para atualização de status de projeto."""
    nome: Optional[str] = Field(None, min_length=1, max_length=50)
    descricao: Optional[str] = Field(None, max_length=255)
    is_final: Optional[bool] = None
    ordem_exibicao: Optional[int] = None


class StatusProjetoResponseSchema(BaseResponseSchema):
    """Schema para resposta com dados de status de projeto."""
    nome: str
    descricao: Optional[str] = None
    is_final: bool
    ordem_exibicao: Optional[int] = None 