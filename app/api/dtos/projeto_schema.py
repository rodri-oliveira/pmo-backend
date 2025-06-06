from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel


class ProjetoCreateSchema(BaseModel):  
    """Schema para criação de projeto.
    Campos de data aceitam formatos YYYY-MM-DD ou DD/MM/YYYY quando usados como filtro.
    """
    nome: str
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto_id: int
    secao_id: Optional[int] = None
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    ativo: bool = True

class ProjetoUpdateSchema(BaseModel):
    """Schema para atualização de projeto."""
    nome: Optional[str] = None
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto_id: Optional[int] = None
    secao_id: Optional[int] = None
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    ativo: Optional[bool] = None

class StatusProjetoSchema(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    is_final: Optional[bool] = None
    ordem_exibicao: Optional[int] = None

    class Config:
        from_attributes = True

class ProjetoResponseSchema(BaseModel):
    """Schema para resposta com dados de projeto.
    Campos de data aceitam formatos YYYY-MM-DD ou DD/MM/YYYY quando usados como filtro.
    """
    id: int
    nome: str
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto: StatusProjetoSchema
    status_projeto_id: int
    secao_id: Optional[int] = None
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    data_criacao: datetime
    data_atualizacao: datetime
    ativo: bool

    class Config:
        from_attributes = True