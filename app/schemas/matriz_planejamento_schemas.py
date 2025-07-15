from pydantic import BaseModel, Field
from typing import List, Optional


class PlanejamentoHorasCreate(BaseModel):
    alocacao_id: int
    ano: int
    mes: int
    horas_planejadas: float

class PlanejamentoMensalUpdate(BaseModel):
    mes: int = Field(..., ge=1, le=12)
    horas_planejadas: float = Field(..., ge=0)

class ProjetoUpdate(BaseModel):
    projeto_id: int
    status_alocacao_id: Optional[int] = None
    observacao: Optional[str] = None
    esforco_estimado: Optional[float] = None
    planejamento_mensal: List[PlanejamentoMensalUpdate] = []

class MatrizPlanejamentoUpdate(BaseModel):
    recurso_id: int
    ano: int
    alteracoes_projetos: List[ProjetoUpdate]
