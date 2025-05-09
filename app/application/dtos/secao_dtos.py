from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SecaoBaseDTO(BaseModel):
    nome: str
    descricao: Optional[str] = None

class SecaoCreateDTO(SecaoBaseDTO):
    pass

class SecaoUpdateDTO(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None

class SecaoDTO(SecaoBaseDTO):
    id: int
    ativo: bool
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        from_attributes = True # Pydantic V2 uses from_attributes=True
        # For Pydantic V2, it should be:
        # model_config = {
        #     "from_attributes": True
        # }

