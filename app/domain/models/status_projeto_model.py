from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StatusProjeto(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    is_final: bool
    ordem_exibicao: Optional[int] = None
    data_criacao: datetime
    data_atualizacao: datetime

