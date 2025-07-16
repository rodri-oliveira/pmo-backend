from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_async_db
from app.services.relatorio_service import RelatorioService
from app.models.schemas import HorasDisponiveisRequest, HorasDisponiveisResponse

router = APIRouter()

@router.post(
    "/horas-disponiveis-recurso",
    response_model=HorasDisponiveisResponse,
    summary="Consultar Horas Disponíveis de um Recurso",
    description="Retorna o total de horas de trabalho disponíveis por mês para um recurso específico, dentro de um intervalo de datas.",
    status_code=status.HTTP_200_OK
)
async def get_horas_disponiveis_recurso(
    request: HorasDisponiveisRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Endpoint para consultar as horas disponíveis de um recurso em um determinado período.

    - **recurso_id**: ID do recurso a ser consultado.
    - **data_inicio**: Mês de início da consulta (formato: AAAA-MM).
    - **data_fim**: Mês de fim da consulta (formato: AAAA-MM).
    """
    service = RelatorioService(db)
    horas_response = await service.get_horas_disponiveis_recurso(request)

    if not horas_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurso com ID {request.recurso_id} não encontrado."
        )

    return horas_response
