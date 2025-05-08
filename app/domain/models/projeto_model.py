from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class Projeto(BaseModel):
    id: int
    nome: str
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto_id: int
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    ativo: bool
    data_criacao: datetime
    data_atualizacao: datetime

