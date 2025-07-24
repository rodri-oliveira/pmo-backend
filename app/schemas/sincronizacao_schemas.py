"""
Schemas para sincronização Jira com parâmetros de data flexíveis
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from typing import Optional, List


class SincronizacaoJiraRequest(BaseModel):
    """Schema para requisição de sincronização Jira"""
    data_inicio: date = Field(..., description="Data de início da sincronização (YYYY-MM-DD)")
    data_fim: date = Field(..., description="Data de fim da sincronização (YYYY-MM-DD)")
    projetos: Optional[List[str]] = Field(
        default=["DTIN", "SGI", "TIN", "SEG"], 
        description="Lista de projetos Jira para sincronizar"
    )

    @validator('data_fim')
    def validar_data_fim(cls, v, values):
        if 'data_inicio' in values and v < values['data_inicio']:
            raise ValueError('Data fim deve ser maior ou igual à data início')
        return v

    @validator('data_inicio', 'data_fim')
    def validar_data_nao_futura(cls, v):
        if v > date.today():
            raise ValueError('Data não pode ser futura')
        return v

    @validator('projetos')
    def validar_projetos(cls, v):
        if v and len(v) == 0:
            raise ValueError('Lista de projetos não pode estar vazia')
        projetos_validos = ["DTIN", "SGI", "TIN", "SEG"]
        for projeto in v or []:
            if projeto not in projetos_validos:
                raise ValueError(f'Projeto {projeto} não é válido. Projetos válidos: {projetos_validos}')
        return v


class SincronizacaoJiraResponse(BaseModel):
    """Schema para resposta de sincronização Jira"""
    status: str = Field(..., description="Status da sincronização (success, error, processing)")
    periodo: dict = Field(..., description="Período sincronizado")
    resultados: dict = Field(..., description="Estatísticas da sincronização")
    tempo_execucao: Optional[str] = Field(None, description="Tempo de execução")
    mensagem: Optional[str] = Field(None, description="Mensagem adicional")
    erro: Optional[str] = Field(None, description="Detalhes do erro, se houver")


class SincronizacaoJiraStatus(BaseModel):
    """Schema para status de sincronização em andamento"""
    status: str = Field(..., description="Status atual (processing, completed, error)")
    progresso: Optional[int] = Field(None, description="Progresso em porcentagem (0-100)")
    issues_processadas: Optional[int] = Field(None, description="Número de issues processadas")
    tempo_decorrido: Optional[str] = Field(None, description="Tempo decorrido desde o início")
    estimativa_conclusao: Optional[str] = Field(None, description="Estimativa de conclusão")
