from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StatusProjetoBaseDTO(BaseModel):
    nome: str
    descricao: Optional[str] = None
    is_final: bool = False
    ordem_exibicao: Optional[int] = None

class StatusProjetoCreateRequestDTO(BaseModel):
    nome: str
    descricao: Optional[str] = None
    is_final: bool = False

class StatusProjetoCreateDTO(StatusProjetoBaseDTO):
    pass

class StatusProjetoUpdateDTO(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    is_final: Optional[bool] = None
    ordem_exibicao: Optional[int] = None

class StatusProjetoDTO(StatusProjetoBaseDTO):
    id: int
    data_criacao: datetime
    data_atualizacao: datetime

    model_config = {'from_attributes': True}

