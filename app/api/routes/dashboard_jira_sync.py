"""
Endpoints para Sincronização do Dashboard Jira
Permite executar sincronização via API REST
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.services.dashboard_jira_sync_script import DashboardJiraSyncScript
from app.services.dashboard_jira_query_service import DashboardJiraQueryService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/sync/all")
async def trigger_sync_all(
    force_refresh: bool = Query(False, description="Forçar sincronização mesmo se cache recente"),
    background_tasks: BackgroundTasks = None,
    run_async: bool = Query(False, description="Executar em background")
):
    """
    Endpoint para sincronizar todas as seções do dashboard Jira
    
    Args:
        force_refresh: Se True, força sincronização mesmo com cache recente
        run_async: Se True, executa em background e retorna imediatamente
    """
    try:
        logger.info(f"[SYNC_ALL_ENDPOINT] Iniciando sincronização completa - force: {force_refresh}, async: {run_async}")
        
        script = DashboardJiraSyncScript()
        
        if run_async and background_tasks:
            # Executar em background
            background_tasks.add_task(script.executar_sincronizacao_completa, force_refresh)
            return {
                "status": "started",
                "message": "Sincronização iniciada em background",
                "timestamp": datetime.now(),
                "force_refresh": force_refresh
            }
        else:
            # Executar síncrono
            resultado = await script.executar_sincronizacao_completa(force_refresh=force_refresh)
            
            return {
                "status": "completed",
                "message": "Sincronização concluída com sucesso",
                "resultado": resultado,
                "stats": script.get_stats()
            }
        
    except Exception as e:
        logger.error(f"[SYNC_ALL_ERROR] Erro no endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na sincronização: {str(e)}")

@router.post("/sync/secao/{secao}")
async def trigger_sync_secao(
    secao: str,
    force_refresh: bool = Query(False, description="Forçar sincronização mesmo se cache recente"),
    background_tasks: BackgroundTasks = None,
    run_async: bool = Query(False, description="Executar em background")
):
    """
    Endpoint para sincronizar uma seção específica do dashboard Jira
    
    Args:
        secao: Seção a ser sincronizada (DTIN, SEG, SGI)
        force_refresh: Se True, força sincronização mesmo com cache recente
        run_async: Se True, executa em background
    """
    try:
        # Validar seção
        if secao.upper() not in ['DTIN', 'SEG', 'SGI']:
            raise HTTPException(status_code=400, detail=f"Seção inválida: {secao}. Deve ser DTIN, SEG ou SGI")
        
        logger.info(f"[SYNC_SECAO_ENDPOINT] Iniciando sincronização da seção {secao} - force: {force_refresh}")
        
        script = DashboardJiraSyncScript()
        
        if run_async and background_tasks:
            # Executar em background
            background_tasks.add_task(script.executar_sincronizacao_secao, secao.upper(), force_refresh)
            return {
                "status": "started",
                "message": f"Sincronização da seção {secao} iniciada em background",
                "secao": secao.upper(),
                "timestamp": datetime.now(),
                "force_refresh": force_refresh
            }
        else:
            # Executar síncrono
            resultado = await script.executar_sincronizacao_secao(secao.upper(), force_refresh=force_refresh)
            
            return {
                "status": "completed",
                "message": f"Sincronização da seção {secao} concluída",
                "secao": secao.upper(),
                "resultado": resultado,
                "stats": script.get_stats()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SYNC_SECAO_ERROR] Erro no endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na sincronização da seção {secao}: {str(e)}")

@router.get("/status")
async def get_sync_status(db: AsyncSession = Depends(get_async_db)):
    """
    Endpoint para verificar o status atual do cache do dashboard
    """
    try:
        logger.info("[SYNC_STATUS_ENDPOINT] Consultando status do cache")
        
        query_service = DashboardJiraQueryService(db)
        status = await query_service.get_status_cache()
        
        # Verificar quais seções precisam de sincronização
        necessita_sync = await query_service.verificar_necessidade_sync(horas_limite=6)
        
        return {
            "status": "success",
            "timestamp": datetime.now(),
            "cache_status": status,
            "necessita_sincronizacao": necessita_sync,
            "recomendacao": {
                "sync_recomendado": any(necessita_sync.values()),
                "secoes_desatualizadas": [k for k, v in necessita_sync.items() if v]
            }
        }
        
    except Exception as e:
        logger.error(f"[SYNC_STATUS_ERROR] Erro no endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao verificar status: {str(e)}")

@router.delete("/cleanup")
async def cleanup_old_snapshots(
    dias_manter: int = Query(7, description="Número de dias de snapshots para manter"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Endpoint para limpar snapshots antigos do cache
    
    Args:
        dias_manter: Número de dias de snapshots para manter (padrão: 7)
    """
    try:
        if dias_manter < 1:
            raise HTTPException(status_code=400, detail="dias_manter deve ser maior que 0")
        
        logger.info(f"[CLEANUP_ENDPOINT] Iniciando limpeza de snapshots com mais de {dias_manter} dias")
        
        query_service = DashboardJiraQueryService(db)
        resultado = await query_service.limpar_cache_antigo(dias_manter=dias_manter)
        
        return {
            "status": "success",
            "message": f"Limpeza concluída com sucesso",
            "timestamp": datetime.now(),
            "dias_mantidos": dias_manter,
            "resultado": resultado
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CLEANUP_ERROR] Erro no endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na limpeza: {str(e)}")

@router.get("/historico")
async def get_sync_historico(
    secao: Optional[str] = Query(None, description="Seção específica (DTIN, SEG, SGI) ou todas"),
    dias: int = Query(7, description="Número de dias de histórico"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Endpoint para obter histórico de sincronizações
    
    Args:
        secao: Seção específica ou None para todas
        dias: Número de dias de histórico
    """
    try:
        if secao and secao.upper() not in ['DTIN', 'SEG', 'SGI']:
            raise HTTPException(status_code=400, detail=f"Seção inválida: {secao}. Deve ser DTIN, SEG ou SGI")
        
        logger.info(f"[HISTORICO_ENDPOINT] Consultando histórico - seção: {secao}, dias: {dias}")
        
        query_service = DashboardJiraQueryService(db)
        historico = await query_service.get_historico_snapshots(
            secao=secao.upper() if secao else None, 
            dias=dias
        )
        
        return {
            "status": "success",
            "timestamp": datetime.now(),
            "filtros": {
                "secao": secao.upper() if secao else "todas",
                "dias": dias
            },
            "total_registros": len(historico),
            "historico": historico
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[HISTORICO_ERROR] Erro ao buscar histórico: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar histórico: {str(e)}")

@router.post("/sync/auto")
async def trigger_auto_sync(
    horas_limite: int = Query(6, description="Limite de horas para considerar cache desatualizado"),
    background_tasks: BackgroundTasks = None
):
    """
    Endpoint para sincronização automática inteligente
    Sincroniza apenas seções que estão desatualizadas
    
    Args:
        horas_limite: Limite de horas para considerar cache desatualizado
    """
    try:
        logger.info(f"[AUTO_SYNC_ENDPOINT] Iniciando sincronização automática - limite: {horas_limite}h")
        
        # Verificar quais seções precisam de sincronização
        async with AsyncSessionLocal() as session:
            query_service = DashboardJiraQueryService(session)
            necessita_sync = await query_service.verificar_necessidade_sync(horas_limite=horas_limite)
        
        secoes_para_sync = [secao for secao, precisa in necessita_sync.items() if precisa]
        
        if not secoes_para_sync:
            return {
                "status": "skipped",
                "message": "Nenhuma seção precisa de sincronização",
                "timestamp": datetime.now(),
                "cache_status": necessita_sync
            }
        
        # Executar sincronização das seções necessárias
        script = DashboardJiraSyncScript()
        resultados = []
        
        for secao in secoes_para_sync:
            try:
                resultado = await script.executar_sincronizacao_secao(secao, force_refresh=True)
                resultados.append(resultado)
                logger.info(f"[AUTO_SYNC] Seção {secao} sincronizada com sucesso")
            except Exception as e:
                logger.error(f"[AUTO_SYNC_ERROR] Erro ao sincronizar {secao}: {str(e)}")
                resultados.append({
                    "secao": secao,
                    "status": "error",
                    "erro": str(e)
                })
        
        return {
            "status": "completed",
            "message": f"Sincronização automática concluída para {len(secoes_para_sync)} seções",
            "timestamp": datetime.now(),
            "secoes_sincronizadas": secoes_para_sync,
            "resultados": resultados,
            "stats": script.get_stats()
        }
        
    except Exception as e:
        logger.error(f"[AUTO_SYNC_ERROR] Erro no endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na sincronização automática: {str(e)}")

# Importar AsyncSessionLocal para uso no auto_sync
from app.db.session import AsyncSessionLocal
