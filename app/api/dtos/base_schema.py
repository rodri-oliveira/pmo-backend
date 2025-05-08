from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """Esquema base para todos os DTOs."""
    
    class Config:
        """Configuração para os schemas Pydantic."""
        from_attributes = True


class BaseResponseSchema(BaseSchema):
    """Esquema base para respostas da API com campos de auditoria."""
    id: int
    data_criacao: datetime
    data_atualizacao: datetime
    ativo: Optional[bool] = True 