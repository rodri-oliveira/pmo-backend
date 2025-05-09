from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_admin_user
from app.db.session import get_db
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

router = APIRouter(prefix="/planejamento-horas", tags=["Planejamento de Horas"])


@router.post("/", response_model=PlanejamentoHorasResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_planejamento(
    planejamento: PlanejamentoHorasCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Cria ou atualiza um planejamento de horas.
    
    Args:
        planejamento: Dados do planejamento
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        PlanejamentoHorasResponse: Dados do planejamento criado/atualizado
    
    Raises:
        HTTPException: Se houver erro na operação
    """
    service = PlanejamentoHorasService(db)
    try:
        result = service.create_or_update_planejamento(
            planejamento.alocacao_id,
            planejamento.ano,
            planejamento.mes,
            planejamento.horas_planejadas
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/alocacao/{alocacao_id}", response_model=List[PlanejamentoHorasResponse])
def list_planejamento_by_alocacao(
    alocacao_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
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
    service = PlanejamentoHorasService(db)
    return service.list_by_alocacao(alocacao_id)


@router.get("/recurso/{recurso_id}", response_model=List[PlanejamentoHorasResponse])
def list_planejamento_by_recurso(
    recurso_id: int = Path(..., gt=0),
    ano: int = Query(..., gt=0),
    mes_inicio: int = Query(1, ge=1, le=12),
    mes_fim: int = Query(12, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Lista planejamentos por recurso em um período.
    
    Args:
        recurso_id: ID do recurso
        ano: Ano
        mes_inicio: Mês inicial
        mes_fim: Mês final
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        List[PlanejamentoHorasResponse]: Lista de planejamentos
    """
    service = PlanejamentoHorasService(db)
    return service.list_by_recurso_periodo(recurso_id, ano, mes_inicio, mes_fim)


@router.delete("/{planejamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_planejamento(
    planejamento_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
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
        service.delete_planejamento(planejamento_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) 