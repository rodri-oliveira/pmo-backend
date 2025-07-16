from pydantic import BaseModel, Field
from typing import List, Optional


class PlanejamentoHorasCreate(BaseModel):
    alocacao_id: int
    ano: int
    mes: int
    horas_planejadas: float

class PlanejamentoMensalUpdate(BaseModel):
    ano: int
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
    alteracoes_projetos: List[ProjetoUpdate]

    class Config:
        json_schema_extra = {
            "example": {
                "recurso_id": 87,
                "alteracoes_projetos": [
                    {
                        "projeto_id": 4312,
                        "status_alocacao_id": 1,
                        "observacao": "Atualização de planejamento multi-ano.",
                        "esforco_estimado": 300,
                        "planejamento_mensal": [
                            {"ano": 2024, "mes": 12, "horas_planejadas": 20},
                            {"ano": 2025, "mes": 1, "horas_planejadas": 40},
                            {"ano": 2025, "mes": 2, "horas_planejadas": 35.5}
                        ]
                    }
                ]
            }
        }
