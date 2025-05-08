from typing import Optional
from pydantic import Field, validator

from .base_schema import BaseSchema, BaseResponseSchema


class SecaoCreateSchema(BaseSchema):
    """Schema para criação de seção."""
    nome: str = Field(..., min_length=1, max_length=100)
    descricao: Optional[str] = None
    ativo: bool = True


class SecaoUpdateSchema(BaseSchema):
    """Schema para atualização de seção."""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = None
    ativo: Optional[bool] = None


class SecaoResponseSchema(BaseResponseSchema):
    """Schema para resposta com dados de seção."""
    nome: str
    descricao: Optional[str] = None 