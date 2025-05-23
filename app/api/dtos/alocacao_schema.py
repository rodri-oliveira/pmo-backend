from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field

class AlocacaoBase(BaseModel):
    """Esquema base para alocação de recurso em projeto.
    Campos de data aceitam formatos YYYY-MM-DD ou DD/MM/YYYY quando usados como filtro.
    """
    recurso_id: int = Field(..., gt=0, description="ID do recurso a ser alocado")
    projeto_id: int = Field(..., gt=0, description="ID do projeto para alocação")
    data_inicio_alocacao: date = Field(..., description="Data de início da alocação")
    data_fim_alocacao: Optional[date] = Field(None, description="Data de fim da alocação (opcional)")

class AlocacaoCreate(AlocacaoBase):
    """Esquema para criação de alocação."""
    pass

class AlocacaoUpdate(BaseModel):
    """Esquema para atualização de alocação.
    Campos de data aceitam formatos YYYY-MM-DD ou DD/MM/YYYY quando usados como filtro.
    """
    recurso_id: Optional[int] = Field(None, gt=0, description="ID do recurso a ser alocado")
    projeto_id: Optional[int] = Field(None, gt=0, description="ID do projeto para alocação")
    data_inicio_alocacao: Optional[date] = Field(None, description="Data de início da alocação")
    data_fim_alocacao: Optional[date] = Field(None, description="Data de fim da alocação")

class AlocacaoResponse(AlocacaoBase):
    """Esquema para resposta de alocação."""
    id: int
    data_criacao: datetime
    data_atualizacao: datetime
    
    # Informações adicionais do recurso
    recurso_nome: Optional[str] = None
    
    # Informações adicionais do projeto
    projeto_nome: Optional[str] = None
    
    class Config:
        from_attributes = True
