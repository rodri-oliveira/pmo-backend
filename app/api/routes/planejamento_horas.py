from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin_user
from app.db.session import get_async_db
from app.services.planejamento_horas_service import PlanejamentoHorasService
import logging
from fastapi.responses import JSONResponse

# DTOs
class PlanejamentoHorasCreate(BaseModel):
    alocacao_id: int
    ano: int
    mes: int
    horas_planejadas: float

class PlanejamentoHorasResponse(BaseModel):
    id: int
    alocacao_id: int
    projeto_id: int
    recurso_id: int
    ano: int
    mes: int
    horas_planejadas: float
    
    class Config:
        from_attributes = True

router = APIRouter(tags=["Planejamento de Horas"])

@router.post("/", response_model=PlanejamentoHorasResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_planejamento(
    planejamento: PlanejamentoHorasCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Cria ou atualiza planejamento de horas.
    
    Args:
        planejamento: Dados do planejamento
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
        
    Returns:
        PlanejamentoHorasResponse: Planejamento criado/atualizado
    """
    try:
        service = PlanejamentoHorasService(db)
        result = await service.create_or_update_planejamento(
            planejamento.alocacao_id,
            planejamento.ano,
            planejamento.mes,
            planejamento.horas_planejadas
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/alocacao/{alocacao_id}", response_model=dict)
async def list_planejamento_by_alocacao(
    alocacao_id: int = Path(..., gt=0),
    ano: Optional[int] = Query(None, gt=0),
    
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Lista planejamentos por alocação.
    
    Args:
        alocacao_id: ID da alocação
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        List[PlanejamentoHorasResponse]: Lista de planejamentos
    """
    logger = logging.getLogger("app.api.routes.planejamento_horas")
    logger.info(f"[list_planejamento_by_alocacao] Início: alocacao_id={alocacao_id}")
    try:
        service = PlanejamentoHorasService(db)
        result = await service.list_by_alocacao(alocacao_id, ano)
        logger.info(f"[list_planejamento_by_alocacao] Sucesso: {len(result)} registros retornados para alocacao_id={alocacao_id}")
        return {"items": result}
    except ValueError as e:
        logger.warning(f"[list_planejamento_by_alocacao] Valor inválido: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[list_planejamento_by_alocacao] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao listar planejamentos por alocação: {str(e)}")

@router.get("/recurso/{recurso_id}", response_model=dict)
async def list_planejamento_by_recurso(
    recurso_id: int = Path(..., gt=0),
    ano: int = Query(..., gt=0),
    mes_inicio: int = Query(1, ge=1, le=12),
    mes_fim: int = Query(12, ge=1, le=12),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Lista planejamentos por recurso em um período.
    """
    logger = logging.getLogger("app.api.routes.planejamento_horas")
    logger.info(f"[list_planejamento_by_recurso] Início: recurso_id={recurso_id}, ano={ano}, mes_inicio={mes_inicio}, mes_fim={mes_fim}")
    try:
        service = PlanejamentoHorasService(db)
        result = await service.list_by_recurso_periodo(recurso_id, ano, mes_inicio, mes_fim)
        logger.info(f"[list_planejamento_by_recurso] Sucesso: {len(result)} registros retornados para recurso_id={recurso_id}")
        return {"items": result}
    except ValueError as e:
        logger.warning(f"[list_planejamento_by_recurso] Valor inválido: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[list_planejamento_by_recurso] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao listar planejamentos por recurso: {str(e)}")

@router.delete("/{planejamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planejamento(
    planejamento_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Remove um planejamento de horas.
    
    Args:
        planejamento_id: ID do planejamento
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Raises:
        HTTPException: Se o planejamento não for encontrado
    """
    service = PlanejamentoHorasService(db)
    try:
        await service.delete_planejamento(planejamento_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))