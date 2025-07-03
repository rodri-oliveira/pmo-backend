import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.db.orm_models import Projeto, Secao

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/projetos-ativos-por-secao", tags=["Dashboard"]) 
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


@router.get("/equipes-ativas-por-secao", tags=["Dashboard"])
async def get_equipes_ativas_por_secao(db: AsyncSession = Depends(get_async_db)):
    """
    Retorna o total de equipes ativas para as seções SGI, SEG e TIN.
    """
    logger.info("--- EXECUTANDO ENDPOINT /equipes-ativas-por-secao ---")
    try:
        id_para_sigla = {1: "SGI", 2: "SEG", 3: "TIN"}
        result = {sigla: 0 for sigla in id_para_sigla.values()}

        raw_sql = text("""
            SELECT secao_id, COUNT(id) as total
            FROM equipe
            WHERE ativo = TRUE AND secao_id IN (1, 2, 3)
            GROUP BY secao_id
        """)

        db_result = (await db.execute(raw_sql)).mappings().all()
        logger.info(f"[RAW SQL RESULT] Resultado do banco (equipes): {db_result}")

        for row in db_result:
            sigla = id_para_sigla.get(row['secao_id'])
            if sigla:
                result[sigla] = row['total']

        logger.info(f"[FINAL] Resultado a ser retornado (equipes): {result}")
        return result

    except Exception as e:
        logger.error(f"ERRO CRÍTICO NO ENDPOINT DE EQUIPES: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/horas-por-secao", tags=["Dashboard"])
async def get_horas_por_secao(db: AsyncSession = Depends(get_async_db)):
    """
    Retorna o total de horas planejadas e apontadas por seção para o ano corrente.
    """
    logger.info("--- EXECUTANDO ENDPOINT /horas-por-secao ---")
    try:
        ano_corrente = datetime.now().year
        id_para_sigla = {1: "SGI", 2: "SEG", 3: "TIN"}
        
        result = { sigla: {"planejado": 0, "apontado": 0} for sigla in id_para_sigla.values() }

        # Query para horas planejadas
        sql_planejado = text(f"""
            SELECT p.secao_id, SUM(hp.horas_planejadas) as total
            FROM horas_planejadas_alocacao hp
            JOIN alocacao_recurso_projeto arp ON hp.alocacao_id = arp.id
            JOIN projeto p ON arp.projeto_id = p.id
            WHERE hp.ano = {ano_corrente} AND p.secao_id IN (1, 2, 3)
            GROUP BY p.secao_id
        """)
        db_planejado = (await db.execute(sql_planejado)).mappings().all()
        for row in db_planejado:
            sigla = id_para_sigla.get(row['secao_id'])
            if sigla:
                result[sigla]["planejado"] = float(row['total'] or 0)

        # Query para horas apontadas
        sql_apontado = text(f"""
            SELECT p.secao_id, SUM(a.horas_apontadas) as total
            FROM apontamento a
            JOIN projeto p ON a.projeto_id = p.id
            WHERE EXTRACT(YEAR FROM a.data_apontamento) = {ano_corrente} AND p.secao_id IN (1, 2, 3)
            GROUP BY p.secao_id
        """)
        db_apontado = (await db.execute(sql_apontado)).mappings().all()
        for row in db_apontado:
            sigla = id_para_sigla.get(row['secao_id'])
            if sigla:
                result[sigla]["apontado"] = float(row['total'] or 0)

        logger.info(f"[FINAL] Resultado de horas por seção: {result}")
        return result

    except Exception as e:
        logger.error(f"ERRO CRÍTICO NO ENDPOINT DE HORAS: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/status-projetos-por-secao", tags=["Dashboard"])
async def get_status_projetos_por_secao(db: AsyncSession = Depends(get_async_db)):
    """
    Retorna a contagem e o percentual de projetos por status para cada seção.
    Garante que todos os status ativos sejam retornados para cada seção, mesmo que com contagem zero.
    Considera apenas projetos ativos.
    """
    logger.info("--- EXECUTANDO ENDPOINT /status-projetos-por-secao (LÓGICA COMPLETA) ---")
    try:
        id_para_sigla = {1: "SGI", 2: "SEG", 3: "TIN"}
        
        result = {
            sigla: {"total_projetos": 0, "status": {}}
            for sigla in id_para_sigla.values()
        }

        sql_query = text("""
            WITH Secoes AS (
                SELECT id FROM (VALUES (1), (2), (3)) AS v(id)
            ),
            StatusAtivos AS (
                SELECT id, nome FROM status_projeto WHERE ativo = TRUE
            ),
            Combinacoes AS (
                SELECT
                    s.id AS secao_id,
                    sa.id AS status_id,
                    sa.nome AS status_nome
                FROM Secoes s
                CROSS JOIN StatusAtivos sa
            ),
            ContagemProjetos AS (
                SELECT
                    p.secao_id,
                    p.status_projeto_id,
                    COUNT(p.id) AS quantidade
                FROM
                    projeto p
                WHERE
                    p.ativo = TRUE
                    AND p.secao_id IN (1, 2, 3)
                GROUP BY
                    p.secao_id, p.status_projeto_id
            )
            SELECT
                c.secao_id,
                c.status_nome,
                COALESCE(cp.quantidade, 0) AS quantidade
            FROM
                Combinacoes c
            LEFT JOIN
                ContagemProjetos cp ON c.secao_id = cp.secao_id AND c.status_id = cp.status_projeto_id
            ORDER BY
                c.secao_id, c.status_nome
        """)
        
        db_result = (await db.execute(sql_query)).mappings().all()
        logger.info(f"[RAW SQL RESULT] Resultado do banco (status projetos completo): {db_result}")

        for row in db_result:
            secao_id = row['secao_id']
            sigla = id_para_sigla.get(secao_id)
            if not sigla:
                continue

            status_nome = row['status_nome']
            quantidade = int(row['quantidade'])
            
            result[sigla]["status"][status_nome] = {"quantidade": quantidade}
            result[sigla]["total_projetos"] += quantidade

        for sigla, data in result.items():
            total_projetos = data["total_projetos"]
            if total_projetos > 0:
                for status_nome, status_data in data["status"].items():
                    quantidade = status_data["quantidade"]
                    percentual = round((quantidade / total_projetos) * 100, 2)
                    result[sigla]["status"][status_nome]["percentual"] = percentual
            else:
                for status_data in data["status"].values():
                    status_data["percentual"] = 0
        
        logger.info(f"[FINAL] Resultado de status de projetos por seção: {result}")
        return result

    except Exception as e:
        logger.error(f"ERRO CRÍTICO NO ENDPOINT DE STATUS DE PROJETOS: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )
