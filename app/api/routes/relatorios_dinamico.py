from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db
from app.services.relatorio_dinamico_service import RelatorioDinamicoService

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

from fastapi import HTTPException
import logging

@router.get("/dinamico", summary="Relatório Dinâmico de Horas")
async def relatorio_dinamico(
    recurso_id: Optional[int] = Query(None, description="ID do recurso para filtrar"),
    equipe_id: Optional[int] = Query(None, description="ID da equipe para filtrar"),
    secao_id: Optional[int] = Query(None, description="ID da seção para filtrar"),
    projeto_id: Optional[int] = Query(None, description="ID do projeto para filtrar"),
    data_inicio: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD ou DD/MM/YYYY)"),
    data_fim: Optional[str] = Query(None, description="Data final (YYYY-MM-DD ou DD/MM/YYYY)"),
    agrupar_por: Optional[List[str]] = Query(
        None,
        description="Campos para agrupar: recurso, equipe, secao, projeto, mes, ano. Ex: agrupar_por=recurso&agrupar_por=mes"
    ),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = RelatorioDinamicoService(db)
        result = await service.get_relatorio(
            recurso_id=recurso_id,
            equipe_id=equipe_id,
            secao_id=secao_id,
            projeto_id=projeto_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            agrupar_por=agrupar_por,
        )
        if not result or all((v is None for v in result[0].values())):
            return {"message": "Nenhum dado encontrado para os filtros informados."}
        return result
    except Exception as e:
        logging.exception("Erro inesperado ao gerar relatório dinâmico")
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar relatório dinâmico: {str(e)}")

@router.get("/horas-disponiveis", summary="Horas Disponíveis do Recurso")
async def horas_disponiveis(
    recurso_id: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    mes: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        service = RelatorioDinamicoService(db)
        result = await service.get_horas_disponiveis(
            recurso_id=recurso_id,
            ano=ano,
            mes=mes
        )
        if not result:
            return {"message": "Nenhum dado encontrado para os filtros informados."}
        return result
    except Exception as e:
        logging.exception("Erro inesperado ao buscar horas disponíveis")
        raise HTTPException(status_code=500, detail=f"Erro interno ao buscar horas disponíveis: {str(e)}")
