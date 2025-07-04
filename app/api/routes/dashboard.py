import logging
from collections import defaultdict
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.db.orm_models import Projeto, Secao
from app.models.schemas import (
    DisponibilidadeRecursoResponse,
    DisponibilidadeMensal,
    DisponibilidadeProjetoDetalhe,
    RecursoInfo,
    ProjetoInfo,
)

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


@router.get(
    "/disponibilidade-recurso",
    response_model=DisponibilidadeRecursoResponse,
    tags=["Dashboard"],
    summary="Obtém a disponibilidade detalhada de um recurso por período."
)
async def get_disponibilidade_recurso(
    recurso_id: int = Query(..., description="ID do recurso a ser consultado."),
    ano: int = Query(..., description="Ano de referência para a consulta."),
    mes_inicio: int = Query(..., ge=1, le=12, description="Mês inicial do período (inclusivo)."),
    mes_fim: int = Query(..., ge=1, le=12, description="Mês final do período (inclusivo)."),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retorna um relatório detalhado da disponibilidade de um recurso para um
    intervalo de meses, mostrando a capacidade total, horas planejadas
    (agregadas e por projeto) e horas livres.
    """
    logger.info(f"--- EXECUTANDO ENDPOINT /disponibilidade-recurso PARA RECURSO ID: {recurso_id} ---")
    if mes_inicio > mes_fim:
        raise HTTPException(status_code=400, detail="O mês de início não pode ser maior que o mês de fim.")

    try:
        # Primeiro, busca o nome do recurso
        recurso_sql = text("SELECT id, nome FROM recurso WHERE id = :recurso_id")
        recurso_result = (await db.execute(recurso_sql, {"recurso_id": recurso_id})).mappings().first()

        if not recurso_result:
            raise HTTPException(status_code=404, detail="Recurso não encontrado")

        # Query principal para buscar dados de capacidade e planejamento
        raw_sql = text(
            """
            SELECT
                hdr.ano,
                hdr.mes,
                hdr.horas_disponiveis_mes AS capacidade_rh,
                p.id AS projeto_id,
                p.nome AS projeto_nome,
                hpa.horas_planejadas
            FROM
                horas_disponiveis_rh hdr
            LEFT JOIN
                alocacao_recurso_projeto arp ON hdr.recurso_id = arp.recurso_id
            LEFT JOIN
                horas_planejadas_alocacao hpa ON arp.id = hpa.alocacao_id
                                              AND hdr.ano = hpa.ano
                                              AND hdr.mes = hpa.mes
            LEFT JOIN
                projeto p ON arp.projeto_id = p.id
            WHERE
                hdr.recurso_id = :recurso_id
                AND hdr.ano = :ano
                AND hdr.mes BETWEEN :mes_inicio AND :mes_fim
            ORDER BY
                hdr.ano, hdr.mes;
        """
        )

        params = {"recurso_id": recurso_id, "ano": ano, "mes_inicio": mes_inicio, "mes_fim": mes_fim}
        db_result = (await db.execute(raw_sql, params)).mappings().all()
        logger.info(f"[RAW SQL RESULT] Resultado do banco: {len(db_result)} linhas")

        # Estrutura para processar os dados
        disponibilidade_por_mes = defaultdict(lambda: {
            "capacidade_rh": 0,
            "alocacoes_detalhadas": defaultdict(lambda: {"horas": 0.0, "nome": ""})
        })

        for row in db_result:
            mes_key = (row['ano'], row['mes'])
            disponibilidade_por_mes[mes_key]["capacidade_rh"] = float(row['capacidade_rh'] or 0)

            if row['projeto_id'] and row['horas_planejadas'] is not None:
                proj_id = row['projeto_id']
                disponibilidade_por_mes[mes_key]["alocacoes_detalhadas"][proj_id]["horas"] += float(row['horas_planejadas'])
                disponibilidade_por_mes[mes_key]["alocacoes_detalhadas"][proj_id]["nome"] = row['projeto_nome']

        # Monta a resposta final no formato do schema
        lista_mensal = []
        for (ano_mes, mes_data) in sorted(disponibilidade_por_mes.items()):
            ano_val, mes_val = ano_mes
            capacidade = mes_data['capacidade_rh']

            if capacidade == 0:
                continue

            detalhes_projeto = [
                DisponibilidadeProjetoDetalhe(
                    projeto=ProjetoInfo(id=pid, nome=pdata["nome"]),
                    horas_planejadas=pdata["horas"]
                ) for pid, pdata in mes_data["alocacoes_detalhadas"].items()
            ]

            total_planejado = sum(p.horas_planejadas for p in detalhes_projeto)
            horas_livres = capacidade - total_planejado
            percentual_alocacao = f"{(total_planejado / capacidade * 100):.1f}%" if capacidade > 0 else "0.0%"

            lista_mensal.append(DisponibilidadeMensal(
                mes=mes_val,
                ano=ano_val,
                capacidade_rh=capacidade,
                total_horas_planejadas=total_planejado,
                horas_livres=horas_livres,
                percentual_alocacao=percentual_alocacao,
                alocacoes_detalhadas=detalhes_projeto
            ))

        response_data = DisponibilidadeRecursoResponse(
            recurso=RecursoInfo(id=recurso_result['id'], nome=recurso_result['nome']),
            disponibilidade_mensal=lista_mensal
        )

        logger.info(f"[FINAL] Resultado a ser retornado: {response_data.model_dump_json(indent=2)}")
        return response_data

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"ERRO CRÍTICO NO ENDPOINT /disponibilidade-recurso: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )
