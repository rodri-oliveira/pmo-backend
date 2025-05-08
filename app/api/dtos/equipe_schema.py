from typing import Optional
from pydantic import Field

from .base_schema import BaseSchema, BaseResponseSchema


class EquipeCreateSchema(BaseSchema):
    """Schema para criação de equipe."""
    secao_id: int
    nome: str = Field(..., min_length=1, max_length=100)
    descricao: Optional[str] = None
    ativo: bool = True


class EquipeUpdateSchema(BaseSchema):
    """Schema para atualização de equipe."""
    secao_id: Optional[int] = None
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = None
    ativo: Optional[bool] = None


class EquipeResponseSchema(BaseResponseSchema):
    """Schema para resposta com dados de equipe."""
    secao_id: int
    nome: str
    descricao: Optional[str] = None 