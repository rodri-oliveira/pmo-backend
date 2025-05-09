from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EquipeBaseDTO(BaseModel):
    nome: str
    descricao: Optional[str] = None
    secao_id: int # Foreign Key

class EquipeCreateDTO(EquipeBaseDTO):
    pass

class EquipeUpdateDTO(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    secao_id: Optional[int] = None
    ativo: Optional[bool] = None

class EquipeDTO(EquipeBaseDTO):
    id: int
    ativo: bool
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        from_attributes = True # Pydantic V1
        # For Pydantic V2, it should be:
        # model_config = {
        #     "from_attributes": True
        # }

