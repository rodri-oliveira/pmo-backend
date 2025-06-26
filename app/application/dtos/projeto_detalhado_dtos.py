from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

class SecaoNestedDTO(BaseModel):
    id: int
    nome: str

    model_config = {
        "from_attributes": True
    }

class StatusProjetoNestedDTO(BaseModel):
    id: int
    nome: str

    model_config = {
        "from_attributes": True
    }

class RecursoNestedDTO(BaseModel):
    id: int
    nome: str

    model_config = {
        "from_attributes": True
    }

class HorasPlanejadasNestedDTO(BaseModel):
    ano: int
    mes: int
    horas: float = Field(alias="horas_planejadas")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

class AlocacaoDetalhadaDTO(BaseModel):
    id: int
    data_inicio_alocacao: date
    data_fim_alocacao: Optional[date]
    recurso: RecursoNestedDTO
    horas_planejadas: List[HorasPlanejadasNestedDTO] = []

    model_config = {
        "from_attributes": True
    }

class ProjetoDetalhadoDTO(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]
    codigo_empresa: Optional[str]
    data_inicio_prevista: Optional[date]
    data_fim_prevista: Optional[date]
    ativo: bool
    secao: Optional[SecaoNestedDTO]
    status_projeto: StatusProjetoNestedDTO = Field(alias="status")
    alocacoes: List[AlocacaoDetalhadaDTO] = []

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }
