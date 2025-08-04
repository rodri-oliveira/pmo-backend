"""
Endpoints para Dashboard Cache - Frontend
Endpoints otimizados para consumo do frontend usando dados da tabela dashboard_jira_snapshot.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.services.dashboard_jira_service import DashboardJiraService
from app.services.dashboard_jira_sync_service import DashboardJiraSyncService
from app.services.dashboard_jira_query_service import DashboardJiraQueryService

logger = logging.getLogger(__name__)

router = APIRouter()

# Schemas para o frontend
class SyncRequest(BaseModel):
    """Request para sincronização do cache"""
    data_inicio: str = Field(..., description="Data início (YYYY-MM-DD)")
    data_fim: str = Field(..., description="Data fim (YYYY-MM-DD)")
    secoes: Optional[List[str]] = Field(default=None, description="Seções específicas (DTIN, SEG, SGI) - default: todas")
    force_refresh: bool = Field(default=False, description="Forçar refresh mesmo se dados existem")

class SecaoResult(BaseModel):
    """Resultado da sincronização de uma seção"""
    status: str
    registros: int
    tempo_segundos: float
    ultima_sincronizacao: datetime
    erro: Optional[str] = None

class SyncResponse(BaseModel):
    """Resposta da sincronização"""
    status: str
    periodo: str
    tempo_total_segundos: float
    timestamp: datetime
    resultados: Dict[str, SecaoResult]

@router.post("/sync", response_model=SyncResponse)
async def sync_dashboard_cache(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_db)
):
    """
    Sincroniza cache do dashboard para frontend
    
    - **data_inicio**: Data início obrigatória (YYYY-MM-DD)
    - **data_fim**: Data fim obrigatória (YYYY-MM-DD)  
    - **secoes**: Lista de seções (opcional - default: todas)
    - **force_refresh**: Forçar refresh (opcional - default: false)
    
    Retorna status detalhado por seção com tempos e registros.
    """
    try:
        logger.info(f"[FRONTEND_SYNC] Iniciando sincronização: {request.data_inicio} a {request.data_fim}")
        
        # Validar datas
        try:
            data_inicio = datetime.strptime(request.data_inicio, "%Y-%m-%d")
            data_fim = datetime.strptime(request.data_fim, "%Y-%m-%d")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Formato de data inválido: {str(e)}")
        
        if data_inicio > data_fim:
            raise HTTPException(status_code=400, detail="Data início deve ser menor que data fim")
        
        # Seções padrão se não especificadas
        secoes = request.secoes or ["DTIN", "SEG", "SGI"]
        
        # Validar seções
        secoes_validas = {"DTIN", "SEG", "SGI"}
        secoes_invalidas = set(secoes) - secoes_validas
        if secoes_invalidas:
            raise HTTPException(
                status_code=400, 
                detail=f"Seções inválidas: {list(secoes_invalidas)}. Válidas: {list(secoes_validas)}"
            )
        
        # Inicializar serviços
        jira_service = DashboardJiraService()
        sync_service = DashboardJiraSyncService(jira_service, session)
        
        # Executar sincronização
        inicio_total = datetime.now()
        resultados = {}
        
        for secao in secoes:
            logger.info(f"[FRONTEND_SYNC] Sincronizando seção: {secao}")
            inicio_secao = datetime.now()
            
            try:
                # Sincronizar seção
                from app.models.schemas import SecaoEnum
                secao_enum = SecaoEnum(secao)
                resultado = await sync_service.sync_secao_especifica(
                    secao=secao_enum,
                    force_refresh=request.force_refresh
                )
                
                fim_secao = datetime.now()
                tempo_secao = (fim_secao - inicio_secao).total_seconds()
                
                resultados[secao] = SecaoResult(
                    status="success",
                    registros=resultado.get("registros", 0),
                    tempo_segundos=tempo_secao,
                    ultima_sincronizacao=fim_secao,
                    erro=None
                )
                
                logger.info(f"[FRONTEND_SYNC] {secao} concluída: {resultado.get('registros', 0)} registros em {tempo_secao:.1f}s")
                
            except Exception as e:
                fim_secao = datetime.now()
                tempo_secao = (fim_secao - inicio_secao).total_seconds()
                
                resultados[secao] = SecaoResult(
                    status="error",
                    registros=0,
                    tempo_segundos=tempo_secao,
                    ultima_sincronizacao=fim_secao,
                    erro=str(e)
                )
                
                logger.error(f"[FRONTEND_SYNC] Erro na seção {secao}: {str(e)}")
        
        fim_total = datetime.now()
        tempo_total = (fim_total - inicio_total).total_seconds()
        
        # Status geral
        status_geral = "completed" if all(r.status == "success" for r in resultados.values()) else "partial"
        
        response = SyncResponse(
            status=status_geral,
            periodo=f"{request.data_inicio} a {request.data_fim}",
            tempo_total_segundos=tempo_total,
            timestamp=fim_total,
            resultados=resultados
        )
        
        logger.info(f"[FRONTEND_SYNC] Concluída: {status_geral} em {tempo_total:.1f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FRONTEND_SYNC_ERROR] Erro inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/status")
async def get_cache_status(
    session: AsyncSession = Depends(get_async_db)
):
    """
    Verifica status do cache por seção
    
    Retorna informações sobre última sincronização, quantidade de dados, etc.
    """
    try:
        query_service = DashboardJiraQueryService(session)
        
        # Buscar status por seção
        status_secoes = {}
        
        for secao in ["DTIN", "SEG", "SGI"]:
            try:
                # Buscar últimos dados da seção
                status = await query_service.get_secao_status(secao)
                status_secoes[secao] = status
                
            except Exception as e:
                status_secoes[secao] = {
                    "status": "error",
                    "erro": str(e),
                    "dados_disponiveis": False
                }
        
        return {
            "timestamp": datetime.now(),
            "secoes": status_secoes,
            "cache_ativo": any(s.get("dados_disponiveis", False) for s in status_secoes.values())
        }
        
    except Exception as e:
        logger.error(f"[CACHE_STATUS_ERROR] Erro: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao verificar status: {str(e)}")
