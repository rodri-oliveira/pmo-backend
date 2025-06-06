from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class ProjetoBaseDTO(BaseModel):
    nome: str
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto_id: int # Foreign Key
    secao_id: int # Foreign Key para a tabela secao
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None

class ProjetoCreateDTO(ProjetoBaseDTO):
    data_criacao: Optional[datetime] = None
    data_atualizacao: Optional[datetime] = None
    ativo: bool = True

class ProjetoUpdateDTO(BaseModel):
    nome: Optional[str] = None
    codigo_empresa: Optional[str] = None
    descricao: Optional[str] = None
    jira_project_key: Optional[str] = None
    status_projeto_id: Optional[int] = None
    secao_id: Optional[int] = None
    data_inicio_prevista: Optional[date] = None
    data_fim_prevista: Optional[date] = None
    ativo: Optional[bool] = None
    
class ProjetoDTO(ProjetoBaseDTO):
    id: int
    ativo: bool
    data_criacao: datetime
    data_atualizacao: datetime

    model_config = {'from_attributes': True}
