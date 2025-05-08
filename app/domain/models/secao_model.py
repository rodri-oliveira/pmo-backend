from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Secao(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    ativo: bool
    data_criacao: datetime
    data_atualizacao: datetime

