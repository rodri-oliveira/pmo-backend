from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date

class RecursoBaseDTO(BaseModel):
    nome: str
    email: EmailStr
    matricula: Optional[str] = None
    cargo: Optional[str] = None
    jira_user_id: Optional[str] = None
    data_admissao: Optional[date] = None
    equipe_principal_id: Optional[int] = None # Foreign Key

class RecursoCreateDTO(RecursoBaseDTO):
    pass

class RecursoUpdateDTO(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    matricula: Optional[str] = None
    cargo: Optional[str] = None
    jira_user_id: Optional[str] = None
    data_admissao: Optional[date] = None
    equipe_principal_id: Optional[int] = None
    ativo: Optional[bool] = None

class RecursoDTO(RecursoBaseDTO):
    id: int
    ativo: bool
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        orm_mode = True # Pydantic V1
        # For Pydantic V2, it should be:
        # model_config = {
        #     "from_attributes": True
        # }

