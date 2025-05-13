from datetime import date
from typing import Optional
from pydantic import Field, EmailStr

from .base_schema import BaseSchema, BaseResponseSchema


class RecursoCreateSchema(BaseSchema):
    """Schema para criação de recurso."""
    nome: str = Field(..., min_length=1, max_length=150)
    email: EmailStr = Field(...)
    equipe_principal_id: Optional[int] = None
    matricula: Optional[str] = Field(None, max_length=50)
    cargo: Optional[str] = Field(None, max_length=100)
    jira_user_id: Optional[str] = Field(None, max_length=100)
    data_admissao: Optional[date] = None
    ativo: bool = True


class RecursoUpdateSchema(BaseSchema):
    """Schema para atualização de recurso."""
    nome: Optional[str] = Field(None, min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    equipe_principal_id: Optional[int] = None
    matricula: Optional[str] = Field(None, max_length=50)
    cargo: Optional[str] = Field(None, max_length=100)
    jira_user_id: Optional[str] = Field(None, max_length=100)
    data_admissao: Optional[date] = None
    ativo: Optional[bool] = None


class RecursoResponseSchema(BaseResponseSchema):
    """Schema para resposta com dados de recurso."""
    nome: str
    email: str
    equipe_principal_id: Optional[int] = None
    matricula: Optional[str] = None
    cargo: Optional[str] = None
    jira_user_id: Optional[str] = None
    data_admissao: Optional[date] = None

    class Config:
        from_attributes = True