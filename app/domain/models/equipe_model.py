from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Equipe(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    secao_id: int
    ativo: bool
    data_criacao: datetime
    data_atualizacao: datetime

