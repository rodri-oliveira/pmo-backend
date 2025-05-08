from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date

class Recurso(BaseModel):
    id: int
    nome: str
    email: EmailStr
    matricula: Optional[str] = None
    cargo: Optional[str] = None
    jira_user_id: Optional[str] = None
    data_admissao: Optional[date] = None
    equipe_principal_id: Optional[int] = None
    ativo: bool
    data_criacao: datetime
    data_atualizacao: datetime

