from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin_user
from app.db.session import get_async_db
from app.services.planejamento_horas_service import PlanejamentoHorasService

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

class PlanejamentoHorasListResponse(BaseModel):
    items: List[PlanejamentoHorasResponse]
    total: int
    skip: int
    limit: int

router = APIRouter(prefix="/planejamento-horas", tags=["Planejamento de Horas"])

@router.post("/", response_model=PlanejamentoHorasResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_planejamento(
    planejamento: PlanejamentoHorasCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Cria ou atualiza planejamento de horas.
    
    Args:
        planejamento: Dados do planejamento
        db: Sessão do banco de dados
        
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

@router.get("/alocacao/{alocacao_id}", response_model=List[PlanejamentoHorasResponse])
async def list_planejamento_by_alocacao(
    alocacao_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Lista planejamentos por alocação.
    
    Args:
        alocacao_id: ID da alocação
        db: Sessão do banco de dados
    
    Returns:
        List[PlanejamentoHorasResponse]: Lista de planejamentos
    """
    try:
        service = PlanejamentoHorasService(db)
        return await service.list_by_alocacao(alocacao_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/recurso/{recurso_id}", response_model=List[PlanejamentoHorasResponse])
async def list_planejamento_by_recurso(
    recurso_id: int = Path(..., gt=0),
    ano: int = Query(..., gt=0),
    mes_inicio: int = Query(1, ge=1, le=12),
    mes_fim: int = Query(12, ge=1, le=12),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Lista planejamentos por recurso em um período.
    
    Args:
        recurso_id: ID do recurso
        ano: Ano
        mes_inicio: Mês inicial
        mes_fim: Mês final
        db: Sessão do banco de dados
    
    Returns:
        List[PlanejamentoHorasResponse]: Lista de planejamentos
    """
    service = PlanejamentoHorasService(db)
    return await service.list_by_recurso_periodo(recurso_id, ano, mes_inicio, mes_fim)

@router.delete("/{planejamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planejamento(
    planejamento_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Remove um planejamento de horas.
    
    Args:
        planejamento_id: ID do planejamento
        db: Sessão do banco de dados
    
    Raises:
        HTTPException: Se o planejamento não for encontrado
    """
    service = PlanejamentoHorasService(db)
    try:
        await service.delete_planejamento(planejamento_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/", response_model=PlanejamentoHorasListResponse)
async def list_all_planejamentos(
    db: AsyncSession = Depends(get_async_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    ano: Optional[int] = Query(None, description="Filtrar por ano"),
    mes: Optional[int] = Query(None, ge=1, le=12, description="Filtrar por mês"),
    recurso_id: Optional[int] = Query(None, description="Filtrar por ID do recurso"),
    projeto_id: Optional[int] = Query(None, description="Filtrar por ID do projeto")
):
    """
    Lista todos os planejamentos de horas com filtros e paginação.
    Ideal para relatórios.
    """
    service = PlanejamentoHorasService(db)
    items, total = await service.list_planejamentos_com_filtros_e_paginacao(
        skip=skip, limit=limit, ano=ano, mes=mes, recurso_id=recurso_id, projeto_id=projeto_id
    )
    return PlanejamentoHorasListResponse(items=items, total=total, skip=skip, limit=limit)