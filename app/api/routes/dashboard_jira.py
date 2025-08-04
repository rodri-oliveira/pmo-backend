"""
Rotas para Dashboard JIRA - Indicadores do Departamento
Endpoints para dashboards filtráveis baseados em dados do Jira.
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.services.dashboard_jira_service import DashboardJiraService, DashboardFilters
from app.services.dashboard_jira_query_service import DashboardJiraQueryService
from app.services.dashboard_jira_sync_service import DashboardJiraSyncService
from app.integrations.jira_client import JiraClient
from app.models.schemas import (
    DashboardResponse,
    DashboardFilters as DashboardFiltersSchema,
    RecursosDisponiveisResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/demandas", response_model=DashboardResponse)
async def get_demandas_dashboard(
    secao: Optional[str] = Query(None, description="Seção: DTIN, SEG ou SGI"),
    data_inicio: Optional[str] = Query(None, description="Data de início (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data de fim (YYYY-MM-DD)"),
    ano: Optional[int] = Query(2025, description="Ano para filtro padrão"),
    recursos: Optional[List[str]] = Query(None, description="Lista de jira_user_ids"),
    use_cache: bool = Query(True, description="Usar cache (True) ou consulta direta ao Jira (False)"),
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint para obter dashboard de Demandas (Portfólio)"""
    try:
        logger.info(f"[DEMANDAS_ENDPOINT] Recebendo requisição com parâmetros: secao={secao}, use_cache={use_cache}")
        
        # Validar e processar seção
        secao_processada = None
        if secao:
            # Se contém vírgula, pegar apenas a primeira seção
            if ',' in secao:
                secao_processada = secao.split(',')[0].strip()
                logger.warning(f"[DEMANDAS_ENDPOINT] Múltiplas seções detectadas, usando apenas: {secao_processada}")
            else:
                secao_processada = secao.strip()
            
            # Remover aspas se existirem
            secao_processada = secao_processada.strip('"\'')
            
            # Validar seção
            secoes_validas = ['DTIN', 'SEG', 'SGI']
            if secao_processada not in secoes_validas:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Seção inválida: {secao_processada}. Válidas: {secoes_validas}"
                )
        
        # Criar filtros
        filtros = DashboardFilters(
            secao=secao_processada,
            data_inicio=data_inicio,
            data_fim=data_fim,
            ano=ano,
            recursos=recursos
        )
        
        if use_cache:
            # Usar cache (rápido)
            query_service = DashboardJiraQueryService(db)
            resultado = await query_service.get_demandas_dashboard_cached(filtros)
            
            # Se cache está vazio e seção foi especificada, sugerir sincronização
            if resultado.total == 0 and secao_processada:
                logger.warning(f"[DEMANDAS_CACHE_EMPTY] Cache vazio para seção {secao_processada}. Considere sincronizar primeiro.")
                # Adicionar informação útil na resposta
                resultado.filtros_aplicados["cache_status"] = "empty"
                resultado.filtros_aplicados["sugestao"] = f"Execute POST /backend/dashboard-cache/sync com secoes=['{secao_processada}'] para popular o cache"
        else:
            # Consulta direta ao Jira (lento)
            service = DashboardJiraService()
            resultado = await service.get_demandas_dashboard(filtros)
        
        logger.info(f"[DEMANDAS_SUCCESS] Dashboard retornado com {len(resultado.items)} itens (cache: {use_cache})")
        return resultado
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except ValueError as e:
        logger.error(f"[DEMANDAS_VALIDATION_ERROR] Erro de validação: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro de validação: {str(e)}")
    except Exception as e:
        logger.error(f"[DEMANDAS_ERROR] Erro inesperado no endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor. Verifique os logs para mais detalhes.")

@router.get("/melhorias", response_model=DashboardResponse)
async def get_melhorias_dashboard(
    secao: Optional[str] = Query(None, description="Seção: DTIN, SEG ou SGI"),
    data_inicio: Optional[str] = Query(None, description="Data de início (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data de fim (YYYY-MM-DD)"),
    ano: Optional[int] = Query(2025, description="Ano para filtro padrão"),
    recursos: Optional[List[str]] = Query(None, description="Lista de jira_user_ids"),
    use_cache: bool = Query(True, description="Usar cache (True) ou consulta direta ao Jira (False)"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Dashboard de Melhorias - Epics com label TIN-Melhorias.
    
    Baseado no JQL: TIN-Melhorias 2025
    """
    try:
        logger.info(f"[MELHORIAS_DASHBOARD] Iniciando consulta - seção: {secao}, data_inicio: {data_inicio}, data_fim: {data_fim}, ano: {ano}")
        
        # Criar filtros
        filters = DashboardFilters(
            secao=secao,
            data_inicio=data_inicio,
            data_fim=data_fim,
            ano=ano
        )
        
        # Executar consulta
        service = DashboardJiraService()
        result = await service.get_melhorias_dashboard(filters)
        
        logger.info(f"[MELHORIAS_DASHBOARD] Resultado: {result.total} melhorias encontradas")
        return result
        
    except Exception as e:
        logger.error(f"[MELHORIAS_DASHBOARD_ERROR] Erro: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )

@router.get("/recursos-alocados", response_model=DashboardResponse, tags=["Dashboard Jira"])
async def get_recursos_alocados_dashboard(
    secao: Optional[str] = Query(None, description="Seção: DTIN, SEG ou SGI"),
    recursos: Optional[str] = Query(None, description="Lista de jira_user_ids separados por vírgula"),
    data_inicio: Optional[datetime] = Query(None, description="Data de início (YYYY-MM-DD)"),
    data_fim: Optional[datetime] = Query(None, description="Data de fim (YYYY-MM-DD)"),
    ano: Optional[int] = Query(None, description="Ano para filtro padrão (se datas não especificadas)"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Dashboard de Recursos Alocados (Atividades) - Issues por assignee em outras áreas.
    
    Baseado no JQL: TIN-Recursos Alocados Outras Áreas 2025 - Status
    """
    try:
        logger.info(f"[RECURSOS_DASHBOARD] Iniciando consulta - seção: {secao}, recursos: {recursos}, data_inicio: {data_inicio}, data_fim: {data_fim}, ano: {ano}")
        
        # Processar lista de recursos
        recursos_list = None
        if recursos:
            recursos_list = [r.strip() for r in recursos.split(",") if r.strip()]
        
        # Criar filtros
        filters = DashboardFilters(
            secao=secao,
            recursos=recursos_list,
            data_inicio=data_inicio,
            data_fim=data_fim,
            ano=ano
        )
        
        # Executar consulta
        service = DashboardJiraService()
        result = await service.get_recursos_alocados_dashboard(filters)
        
        logger.info(f"[RECURSOS_DASHBOARD] Resultado: {result.total} atividades encontradas")
        return result
        
    except Exception as e:
        logger.error(f"[RECURSOS_DASHBOARD_ERROR] Erro: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )

@router.get("/recursos-disponiveis", response_model=RecursosDisponiveisResponse, tags=["Dashboard Jira"])
async def get_recursos_disponiveis(
    secao: Optional[str] = Query(None, description="Seção: DTIN, SEG ou SGI"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Lista de recursos (assignees) disponíveis para filtros por seção.
    
    Útil para popular dropdowns de filtros de recursos.
    """
    try:
        logger.info(f"[RECURSOS_DISPONIVEIS] Buscando recursos para seção: {secao}")
        
        # Executar consulta
        service = DashboardJiraService()
        recursos = await service.get_recursos_disponiveis(secao)
        
        logger.info(f"[RECURSOS_DISPONIVEIS] {len(recursos)} recursos encontrados")
        
        return RecursosDisponiveisResponse(
            secao=secao,
            recursos=recursos
        )
        
    except Exception as e:
        logger.error(f"[RECURSOS_DISPONIVEIS_ERROR] Erro: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )

@router.post("/dashboard-completo", response_model=List[DashboardResponse], tags=["Dashboard Jira"])
async def get_dashboard_completo(
    filters: DashboardFiltersSchema,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retorna todos os 3 dashboards (demandas, melhorias, recursos alocados) com os mesmos filtros.
    
    Útil para carregar o dashboard completo de uma vez.
    """
    try:
        logger.info(f"[DASHBOARD_COMPLETO] Iniciando consulta completa com filtros: {filters}")
        
        # Converter schema para dataclass
        dashboard_filters = DashboardFilters(
            secao=filters.secao,
            recursos=filters.recursos,
            data_inicio=filters.data_inicio,
            data_fim=filters.data_fim,
            ano=filters.ano
        )
        
        # Executar todas as consultas
        service = DashboardJiraService()
        
        # Executar em paralelo (se necessário, pode ser sequencial)
        demandas_result = await service.get_demandas_dashboard(dashboard_filters)
        melhorias_result = await service.get_melhorias_dashboard(dashboard_filters)
        recursos_result = await service.get_recursos_alocados_dashboard(dashboard_filters)
        
        results = [demandas_result, melhorias_result, recursos_result]
        
        total_items = sum(r.total for r in results)
        logger.info(f"[DASHBOARD_COMPLETO] Resultado: {total_items} items totais encontrados")
        
        return results
        
    except Exception as e:
        logger.error(f"[DASHBOARD_COMPLETO_ERROR] Erro: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )
