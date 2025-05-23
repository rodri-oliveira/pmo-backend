from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db
from app.services.relatorio_dinamico_service import RelatorioDinamicoService

print(">>> relatorios_dinamico.py carregado <<<")
router = APIRouter(prefix="/relatorios-dinamico")

@router.get("/dinamico", tags=["Relatórios"], summary="Relatório Dinâmico de Horas")
async def relatorio_dinamico(
    recurso_id: Optional[int] = Query(None),
    equipe_id: Optional[int] = Query(None),
    secao_id: Optional[int] = Query(None),
    projeto_id: Optional[int] = Query(None),
    data_inicio: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD ou DD/MM/YYYY)"),
    data_fim: Optional[str] = Query(None, description="Data final (YYYY-MM-DD ou DD/MM/YYYY)"),
    agrupar_por: Optional[List[str]] = Query(None, description="Ex: recurso, equipe, secao, projeto, mes, ano"),
    db: AsyncSession = Depends(get_async_db),
):
    service = RelatorioDinamicoService(db)
    return await service.get_relatorio(
        recurso_id=recurso_id,
        equipe_id=equipe_id,
        secao_id=secao_id,
        projeto_id=projeto_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        agrupar_por=agrupar_por,
    )

@router.get("/horas-disponiveis", tags=["Relatórios"], summary="Horas Disponíveis do Recurso")
async def horas_disponiveis(
    recurso_id: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    mes: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    service = RelatorioDinamicoService(db)
    return await service.get_horas_disponiveis(
        recurso_id=recurso_id,
        ano=ano,
        mes=mes
    )
