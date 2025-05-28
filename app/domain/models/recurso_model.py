from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class Recurso(BaseModel):
    id: int
    nome: str
    email: Optional[str] = None
    matricula: Optional[str]
    cargo: Optional[str]
    jira_user_id: Optional[str]
    data_admissao: Optional[date]
    equipe_principal_id: Optional[int]
    ativo: bool
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        from_attributes = True