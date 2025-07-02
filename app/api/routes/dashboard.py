import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.db.orm_models import Projeto, Secao

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/projetos-ativos-por-secao")
async def get_projetos_ativos_por_secao(db: AsyncSession = Depends(get_async_db)):
    """
    Retorna o total de projetos ativos para as seções SGI, SEG e TIN usando SQL puro.
    """
    logger.info("--- EXECUTANDO ENDPOINT /projetos-ativos-por-secao ---")
    try:
        id_para_sigla = {1: "SGI", 2: "SEG", 3: "TIN"}
        result = {sigla: 0 for sigla in id_para_sigla.values()}

        raw_sql = text("""
            SELECT secao_id, COUNT(id) as total
            FROM projeto
            WHERE ativo = TRUE AND secao_id IN (1, 2, 3)
            GROUP BY secao_id
        """)

        db_result = (await db.execute(raw_sql)).mappings().all()
        logger.info(f"[RAW SQL RESULT] Resultado do banco: {db_result}")

        for row in db_result:
            sigla = id_para_sigla.get(row['secao_id'])
            if sigla:
                result[sigla] = row['total']

        logger.info(f"[FINAL] Resultado a ser retornado: {result}")
        return result

    except Exception as e:
        logger.error(f"ERRO CRÍTICO NO ENDPOINT: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )
