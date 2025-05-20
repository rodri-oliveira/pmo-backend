from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel


class ProjetoCreateSchema(BaseModel):  # <-- precisa herdar de BaseModel
    nome: str
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto_id: int
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    ativo: bool = True

class StatusProjetoSchema(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    is_final: Optional[bool] = None
    ordem_exibicao: Optional[int] = None

    class Config:
        from_attributes = True

class ProjetoResponseSchema(BaseModel):
    id: int
    nome: str
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto: StatusProjetoSchema
    status_projeto_id: int
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    data_criacao: datetime
    data_atualizacao: datetime
    ativo: bool

    class Config:
        from_attributes = True