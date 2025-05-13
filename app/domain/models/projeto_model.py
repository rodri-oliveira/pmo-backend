from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel

class Projeto(BaseModel):
    id: int
    nome: str
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto_id: int
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    data_criacao: Optional[datetime] = None
    data_atualizacao: Optional[datetime] = None
    ativo: bool
    
    class Config:
        from_attributes = True