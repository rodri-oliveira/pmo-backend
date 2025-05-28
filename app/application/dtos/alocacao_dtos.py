from typing import Optional
from datetime import date
from pydantic import BaseModel

class AlocacaoCreateDTO(BaseModel):
    recurso_id: int
    projeto_id: int
    data_inicio_alocacao: date
    data_fim_alocacao: Optional[date]
    status_alocacao_id: Optional[int] = None
    observacao: Optional[str] = None
    # equipe_id será preenchido automaticamente no backend

class AlocacaoUpdateDTO(BaseModel):
    data_inicio_alocacao: Optional[date]
    data_fim_alocacao: Optional[date]
    status_alocacao_id: Optional[int] = None
    observacao: Optional[str] = None
    # equipe_id não é editável pelo usuário

class AlocacaoResponseDTO(BaseModel):
    id: int
    recurso_id: int
    projeto_id: int
    equipe_id: int
    data_inicio_alocacao: date
    data_fim_alocacao: Optional[date]
    status_alocacao_id: Optional[int] = None
    observacao: Optional[str] = None
    equipe_nome: Optional[str] = None
    projeto_nome: Optional[str] = None
    recurso_nome: Optional[str] = None
    # outros campos relevantes

    class Config:
        orm_mode = True
