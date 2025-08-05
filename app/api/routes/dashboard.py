import logging
from collections import defaultdict
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from difflib import SequenceMatcher

from app.db.session import get_async_db
from app.db.orm_models import Projeto, Secao
from app.models.schemas import (
    DisponibilidadeRecursoResponse,
    DisponibilidadeMensal,
    DisponibilidadeProjetoDetalhe,
    RecursoInfo,
    ProjetoInfo,
    DisponibilidadeEquipeResponse,
    RecursoAlocacaoEquipe,
    AlocacaoMensalEquipe,
    AlocacaoProjetoResponse,
    KpisProjeto,
    AlocacaoMensalProjeto,
    DetalheRecursoProjeto,
)

logger = logging.getLogger(__name__)

router = APIRouter()

def encontrar_melhor_match_nome(nome_procurado: str, nomes_disponiveis: List[str], threshold: float = 0.6) -> Optional[str]:
    """
    Encontra o melhor match por similaridade entre nomes de projetos.
    
    Args:
        nome_procurado: Nome do projeto a ser procurado
        nomes_disponiveis: Lista de nomes disponíveis para matching
        threshold: Limiar mínimo de similaridade (0.0 a 1.0)
        
    Returns:
        Nome com melhor match ou None se não encontrar match acima do threshold
    """
    if not nome_procurado or not nomes_disponiveis:
        return None
    
    melhor_match = None
    melhor_score = 0.0
    
    nome_procurado_norm = nome_procurado.strip().upper()
    
    for nome_disponivel in nomes_disponiveis:
        nome_disponivel_norm = nome_disponivel.strip().upper()
        
        # Calcular similaridade
        score = SequenceMatcher(None, nome_procurado_norm, nome_disponivel_norm).ratio()
        
        # Log para debug
        logger.debug(f"[SIMILARITY] '{nome_procurado_norm}' vs '{nome_disponivel_norm}': {score:.3f}")
        
        if score > melhor_score and score >= threshold:
            melhor_score = score
            melhor_match = nome_disponivel
    
    if melhor_match:
        logger.info(f"[MATCH_ENCONTRADO] '{nome_procurado}' → '{melhor_match}' (score: {melhor_score:.3f})")
    else:
        logger.warning(f"[MATCH_NAO_ENCONTRADO] '{nome_procurado}' (threshold: {threshold})")
    
    return melhor_match

@router.get("/projetos-ativos-por-secao", tags=["Dashboard"]) 
async def get_projetos_ativos_por_secao(
    ano: int = Query(2025, description="Ano de referência para filtrar os dados"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retorna o total de projetos que possuem alocações com status "Em andamento" para as seções SGI, SEG e TIN.
    
    Args:
        ano: Ano de referência para filtrar os dados (default: 2025)
    """
    logger.info("--- EXECUTANDO ENDPOINT /projetos-ativos-por-secao (BASEADO EM ALOCAÇÕES) ---")
    try:
        id_para_sigla = {1: "SGI", 2: "SEG", 3: "TIN"}
        result = {sigla: 0 for sigla in id_para_sigla.values()}

        raw_sql = text("""
            SELECT p.secao_id, COUNT(DISTINCT p.id) as total
            FROM projeto p
            INNER JOIN alocacao_recurso_projeto arp ON p.id = arp.projeto_id
            WHERE p.ativo = TRUE 
                AND p.secao_id IN (1, 2, 3)
                AND arp.status_alocacao_id = 3
                AND EXTRACT(YEAR FROM arp.data_inicio) <= :ano
                AND (arp.data_fim IS NULL OR EXTRACT(YEAR FROM arp.data_fim) >= :ano)
            GROUP BY p.secao_id
        """)

        db_result = (await db.execute(raw_sql, {"ano": ano})).mappings().all()
        logger.info(f"[RAW SQL RESULT] Projetos com alocações em andamento para ano {ano}: {db_result}")

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


@router.get("/disponibilidade-equipe", response_model=DisponibilidadeEquipeResponse, tags=["Dashboard"])
async def get_disponibilidade_equipe(
    equipe_id: int = Query(..., description="ID da equipe a ser consultada."),
    ano: int = Query(..., description="Ano do período de consulta."),
    mes_inicio: int = Query(..., ge=1, le=12, description="Mês inicial do período."),
    mes_fim: int = Query(..., ge=1, le=12, description="Mês final do período."),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Fornece os dados de percentual de alocação para todos os membros de uma equipe específica,
    dentro de um intervalo de meses, para alimentar o componente "Mapa de Calor".
    """
    logger.info(f"--- EXECUTANDO ENDPOINT /disponibilidade-equipe para equipe_id={equipe_id} ---")
    try:
        # Esta query busca todos os recursos de uma equipe e calcula suas alocações mensais
        # em relação à capacidade registrada para cada mês.
        raw_sql = text("""
            WITH RECURSOS_EQUIPE AS (
                -- Seleciona os recursos ativos da equipe especificada
                SELECT r.id as recurso_id, r.nome as recurso_nome, e.id as equipe_id, e.nome as equipe_nome
                FROM recurso r
                JOIN equipe e ON r.equipe_principal_id = e.id
                WHERE e.id = :equipe_id AND r.ativo = TRUE
            ),
            HORAS_ALOCADAS AS (
                -- Soma as horas planejadas por recurso e mês
                SELECT
                    arp.recurso_id,
                    hpa.mes,
                    SUM(hpa.horas_planejadas) as total_horas_alocadas
                FROM horas_planejadas_alocacao hpa
                JOIN alocacao_recurso_projeto arp ON hpa.alocacao_id = arp.id
                WHERE arp.recurso_id IN (SELECT recurso_id FROM RECURSOS_EQUIPE)
                  AND hpa.ano = :ano
                  AND hpa.mes BETWEEN :mes_inicio AND :mes_fim
                GROUP BY arp.recurso_id, hpa.mes
            ),
            CAPACIDADE_RECURSO AS (
                -- Busca a capacidade mensal de cada recurso
                SELECT
                    recurso_id,
                    mes,
                    horas_disponiveis_mes as capacidade_mensal
                FROM horas_disponiveis_rh
                WHERE recurso_id IN (SELECT recurso_id FROM RECURSOS_EQUIPE)
                  AND ano = :ano
                  AND mes BETWEEN :mes_inicio AND :mes_fim
            )
            -- Junta os dados para o resultado final
            SELECT
                re.recurso_id,
                re.recurso_nome,
                re.equipe_id,
                re.equipe_nome,
                cr.mes,
                COALESCE(ha.total_horas_alocadas, 0) as horas_alocadas,
                cr.capacidade_mensal
            FROM RECURSOS_EQUIPE re
            JOIN CAPACIDADE_RECURSO cr ON re.recurso_id = cr.recurso_id
            LEFT JOIN HORAS_ALOCADAS ha ON re.recurso_id = ha.recurso_id AND cr.mes = ha.mes
            ORDER BY re.recurso_nome, cr.mes;
        """)

        db_result = (await db.execute(
            raw_sql,
            {"equipe_id": equipe_id, "ano": ano, "mes_inicio": mes_inicio, "mes_fim": mes_fim}
        )).mappings().all()

        if not db_result:
            # Se não houver resultados, busca apenas o nome da equipe para uma resposta vazia e amigável
            equipe_info = await db.execute(text("SELECT nome FROM equipe WHERE id = :equipe_id"), {"equipe_id": equipe_id})
            equipe_nome = equipe_info.scalar_one_or_none()
            if not equipe_nome:
                raise HTTPException(status_code=404, detail=f"Equipe com id {equipe_id} não encontrada.")
            return DisponibilidadeEquipeResponse(equipe_id=equipe_id, equipe_nome=equipe_nome, recursos=[])

        # Processa os resultados para agrupar por recurso
        equipe_nome = db_result[0]['equipe_nome']
        recursos_map = defaultdict(lambda: {"recurso_id": None, "recurso_nome": None, "alocacoes": []})

        for row in db_result:
            recurso_id = row['recurso_id']
            if not recursos_map[recurso_id]["recurso_id"]:
                recursos_map[recurso_id]["recurso_id"] = recurso_id
                recursos_map[recurso_id]["recurso_nome"] = row['recurso_nome']

            capacidade = row['capacidade_mensal']
            horas_alocadas = row['horas_alocadas']
            percentual = (horas_alocadas / capacidade * 100) if capacidade and capacidade > 0 else 0

            recursos_map[recurso_id]["alocacoes"].append(
                AlocacaoMensalEquipe(mes=row['mes'], percentual_alocacao=round(percentual, 1))
            )

        # Formata a resposta final de acordo com o schema
        recursos_list = [RecursoAlocacaoEquipe(**data) for data in recursos_map.values()]

        return DisponibilidadeEquipeResponse(
            equipe_id=equipe_id,
            equipe_nome=equipe_nome,
            recursos=recursos_list
        )

    except Exception as e:
        logger.error(f"ERRO CRÍTICO NO ENDPOINT /disponibilidade-equipe: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/alocacao-projeto", response_model=AlocacaoProjetoResponse, tags=["Dashboard"])
async def get_alocacao_projeto(
    projeto_id: int = Query(..., description="ID do projeto a ser analisado."),
    ano: int = Query(..., description="Ano de referência para a análise."),
    mes_inicio: int = Query(..., ge=1, le=12, description="Mês inicial do período."),
    mes_fim: int = Query(..., ge=1, le=12, description="Mês final do período."),
    equipe_id: Optional[int] = Query(None, description="Opcional. Filtra por equipe."),
    secao_id: Optional[int] = Query(None, description="Opcional. Filtra por seção."),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Fornece dados consolidados sobre a alocação de recursos para um projeto específico.
    """
    logger.info(f"--- EXECUTANDO ENDPOINT /alocacao-projeto para projeto_id={projeto_id} ---")
    try:
        # Query base que será estendida com filtros opcionais de forma performática
        query_base = """
            SELECT
                hpa.mes, hpa.ano,
                arp.recurso_id, r.nome as recurso_nome,
                hpa.horas_planejadas,
                COALESCE(hdr.horas_disponiveis_mes, 0) as capacidade_recurso_mes
            FROM horas_planejadas_alocacao hpa
            JOIN alocacao_recurso_projeto arp ON hpa.alocacao_id = arp.id
            JOIN recurso r ON arp.recurso_id = r.id
            JOIN equipe e ON r.equipe_principal_id = e.id
            LEFT JOIN horas_disponiveis_rh hdr ON r.id = hdr.recurso_id AND hpa.ano = hdr.ano AND hpa.mes = hdr.mes
            WHERE arp.projeto_id = :projeto_id
              AND hpa.ano = :ano
              AND hpa.mes BETWEEN :mes_inicio AND :mes_fim
              AND r.ativo = TRUE
              AND hpa.horas_planejadas > 0
        """
        
        params = {'projeto_id': projeto_id, 'ano': ano, 'mes_inicio': mes_inicio, 'mes_fim': mes_fim}

        if equipe_id:
            query_base += " AND e.id = :equipe_id"
            params['equipe_id'] = equipe_id
        if secao_id:
            query_base += " AND e.secao_id = :secao_id"
            params['secao_id'] = secao_id

        # Adiciona ordenação para consistência
        query_base += " ORDER BY r.nome, hpa.mes;"
        
        raw_sql = text(query_base)
        
        db_result = (await db.execute(raw_sql, params)).mappings().all()

        if not db_result:
            raise HTTPException(status_code=404, detail="Nenhuma alocação encontrada para o projeto e filtros fornecidos.")

        # --- Processamento dos Dados --- #

        # 1. KPIs Gerais
        total_horas_planejadas_geral = sum(row['horas_planejadas'] for row in db_result)
        recursos_envolvidos_geral = set(row['recurso_id'] for row in db_result)
        
        capacidade_total_recursos_geral = 0
        recursos_capacidade_map = {}
        for row in db_result:
            key = (row['recurso_id'], row['mes'])
            if key not in recursos_capacidade_map:
                recursos_capacidade_map[key] = row['capacidade_recurso_mes']
        capacidade_total_recursos_geral = sum(recursos_capacidade_map.values())

        media_alocacao_geral = (total_horas_planejadas_geral / capacidade_total_recursos_geral * 100) if capacidade_total_recursos_geral > 0 else 0

        kpis = KpisProjeto(
            total_recursos_envolvidos=len(recursos_envolvidos_geral),
            total_horas_planejadas=round(float(total_horas_planejadas_geral), 2),
            media_alocacao_recursos_percentual=f"{media_alocacao_geral:.2f}%"
        )

        # 2. Alocação Mensal
        alocacao_mensal_map = defaultdict(lambda: {'horas': 0, 'recursos': set()})
        capacidade_mensal_map = defaultdict(lambda: defaultdict(float))
        for row in db_result:
            mes = row['mes']
            alocacao_mensal_map[mes]['horas'] += row['horas_planejadas']
            alocacao_mensal_map[mes]['recursos'].add(row['recurso_id'])
            capacidade_mensal_map[mes][row['recurso_id']] = row['capacidade_recurso_mes']

        alocacao_mensal_list = []
        for mes, data in sorted(alocacao_mensal_map.items()):
            capacidade_do_mes = sum(capacidade_mensal_map[mes][rid] for rid in data['recursos'])
            alocacao_mensal_list.append(
                AlocacaoMensalProjeto(
                    mes=mes, ano=ano,
                    total_horas_planejadas_no_projeto=round(float(data['horas']), 2),
                    total_capacidade_recursos_envolvidos=round(float(capacidade_do_mes), 2),
                    recursos_envolvidos_count=len(data['recursos'])
                )
            )

        # 3. Detalhe por Recurso
        detalhe_recursos_map = defaultdict(lambda: {'nome': '', 'horas': 0})
        for row in db_result:
            recurso_id = row['recurso_id']
            detalhe_recursos_map[recurso_id]['nome'] = row['recurso_nome']
            detalhe_recursos_map[recurso_id]['horas'] += row['horas_planejadas']

        detalhe_recursos_list = [
            DetalheRecursoProjeto(
                recurso_id=rid,
                recurso_nome=data['nome'],
                total_horas_no_projeto=round(float(data['horas']), 2),
                percentual_do_total_projeto=f"{(data['horas'] / total_horas_planejadas_geral * 100):.2f}%" if total_horas_planejadas_geral > 0 else "0.00%"
            ) for rid, data in detalhe_recursos_map.items()
        ]

        return AlocacaoProjetoResponse(
            kpis_projeto=kpis,
            alocacao_mensal=alocacao_mensal_list,
            detalhe_recursos=detalhe_recursos_list
        )

    except Exception as e:
        logger.error(f"ERRO CRÍTICO NO ENDPOINT /alocacao-projeto: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/equipes-ativas-por-secao", tags=["Dashboard"])
async def get_equipes_ativas_por_secao(
    ano: int = Query(2025, description="Ano de referência para filtrar os dados"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retorna o total de equipes que possuem alocações com status "Em andamento" para as seções SGI, SEG e TIN.
    
    Args:
        ano: Ano de referência para filtrar os dados (default: 2025)
    """
    logger.info("--- EXECUTANDO ENDPOINT /equipes-ativas-por-secao (BASEADO EM ALOCAÇÕES) ---")
    try:
        id_para_sigla = {1: "SGI", 2: "SEG", 3: "TIN"}
        result = {sigla: 0 for sigla in id_para_sigla.values()}

        raw_sql = text("""
            SELECT e.secao_id, COUNT(DISTINCT e.id) as total
            FROM equipe e
            INNER JOIN alocacao_recurso_projeto arp ON e.id = arp.equipe_id
            WHERE e.ativo = TRUE 
                AND e.secao_id IN (1, 2, 3)
                AND arp.status_alocacao_id = 3
                AND EXTRACT(YEAR FROM arp.data_inicio) <= :ano
                AND (arp.data_fim IS NULL OR EXTRACT(YEAR FROM arp.data_fim) >= :ano)
            GROUP BY e.secao_id
        """)

        db_result = (await db.execute(raw_sql, {"ano": ano})).mappings().all()
        logger.info(f"[RAW SQL RESULT] Equipes com alocações em andamento para ano {ano}: {db_result}")

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
async def get_horas_por_secao(
    ano: int = Query(2025, description="Ano de referência para filtrar os dados"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retorna o total de horas planejadas e apontadas por seção para o ano especificado.
    Considera apenas alocações com status "Em andamento" (ID 3).
    
    Args:
        ano: Ano de referência para filtrar os dados (default: 2025)
    """
    logger.info(f"--- EXECUTANDO ENDPOINT /horas-por-secao (BASEADO EM ALOCAÇÕES EM ANDAMENTO) - ANO {ano} ---")
    try:
        id_para_sigla = {1: "SGI", 2: "SEG", 3: "TIN"}
        
        result = { sigla: {"planejado": 0, "apontado": 0} for sigla in id_para_sigla.values() }

        # Query para horas planejadas (apenas alocações em andamento)
        sql_planejado = text("""
            SELECT p.secao_id, SUM(hp.horas_planejadas) as total
            FROM horas_planejadas_alocacao hp
            JOIN alocacao_recurso_projeto arp ON hp.alocacao_id = arp.id
            JOIN projeto p ON arp.projeto_id = p.id
            WHERE hp.ano = :ano 
                AND p.secao_id IN (1, 2, 3)
                AND arp.status_alocacao_id = 3
            GROUP BY p.secao_id
        """)
        db_planejado = (await db.execute(sql_planejado, {"ano": ano})).mappings().all()
        for row in db_planejado:
            sigla = id_para_sigla.get(row['secao_id'])
            if sigla:
                result[sigla]["planejado"] = float(row['total'] or 0)

        # Query para horas apontadas (apenas projetos com alocações em andamento)
        sql_apontado = text("""
            SELECT p.secao_id, SUM(a.horas_apontadas) as total
            FROM apontamento a
            JOIN projeto p ON a.projeto_id = p.id
            WHERE EXTRACT(YEAR FROM a.data_apontamento) = :ano 
                AND p.secao_id IN (1, 2, 3)
                AND EXISTS (
                    SELECT 1 FROM alocacao_recurso_projeto arp 
                    WHERE arp.projeto_id = p.id AND arp.status_alocacao_id = 3
                )
            GROUP BY p.secao_id
        """)
        db_apontado = (await db.execute(sql_apontado, {"ano": ano})).mappings().all()
        for row in db_apontado:
            sigla = id_para_sigla.get(row['secao_id'])
            if sigla:
                result[sigla]["apontado"] = float(row['total'] or 0)

        logger.info(f"[FINAL] Resultado de horas por seção (alocações em andamento): {result}")
        return result

    except Exception as e:
        logger.error(f"ERRO CRÍTICO NO ENDPOINT DE HORAS: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/status-projetos-por-secao", tags=["Dashboard"])
async def get_status_projetos_por_secao(
    ano: int = Query(2025, description="Ano de referência para filtrar os dados"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retorna a contagem e o percentual de alocações por status para cada seção.
    Mostra TODOS os status das alocações e seus percentuais.
    Garante que todos os status ativos sejam retornados para cada seção, mesmo que com contagem zero.
    
    Args:
        ano: Ano de referência para filtrar os dados (default: 2025)
    """
    logger.info(f"--- EXECUTANDO ENDPOINT /status-projetos-por-secao (TODOS OS STATUS DAS ALOCAÇÕES) - ANO {ano} ---")
    try:
        id_para_sigla = {1: "SGI", 2: "SEG", 3: "TIN"}
        
        result = {
            sigla: {"total_alocacoes": 0, "status": {}}
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
            ContagemAlocacoes AS (
                SELECT
                    p.secao_id,
                    arp.status_alocacao_id,
                    COUNT(arp.id) AS quantidade
                FROM
                    alocacao_recurso_projeto arp
                INNER JOIN projeto p ON arp.projeto_id = p.id
                WHERE
                    p.ativo = TRUE
                    AND p.secao_id IN (1, 2, 3)
                    AND EXTRACT(YEAR FROM arp.data_inicio) <= :ano
                    AND (arp.data_fim IS NULL OR EXTRACT(YEAR FROM arp.data_fim) >= :ano)
                GROUP BY
                    p.secao_id, arp.status_alocacao_id
            )
            SELECT
                c.secao_id,
                c.status_nome,
                COALESCE(ca.quantidade, 0) AS quantidade
            FROM
                Combinacoes c
            LEFT JOIN
                ContagemAlocacoes ca ON c.secao_id = ca.secao_id AND c.status_id = ca.status_alocacao_id
            ORDER BY
                c.secao_id, c.status_nome
        """)
        
        db_result = (await db.execute(sql_query, {"ano": ano})).mappings().all()
        logger.info(f"[RAW SQL RESULT] Resultado do banco (status alocações em andamento): {db_result}")

        for row in db_result:
            secao_id = row['secao_id']
            sigla = id_para_sigla.get(secao_id)
            if not sigla:
                continue

            status_nome = row['status_nome']
            quantidade = int(row['quantidade'])
            
            result[sigla]["status"][status_nome] = {"quantidade": quantidade}
            result[sigla]["total_alocacoes"] += quantidade

        for sigla, data in result.items():
            total_alocacoes = data["total_alocacoes"]
            if total_alocacoes > 0:
                for status_nome, status_data in data["status"].items():
                    quantidade = status_data["quantidade"]
                    percentual = round((quantidade / total_alocacoes) * 100, 2)
                    result[sigla]["status"][status_nome]["percentual"] = percentual
            else:
                for status_data in data["status"].values():
                    status_data["percentual"] = 0
        
        logger.info(f"[FINAL] Resultado de status de alocações em andamento por seção: {result}")
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
                -- Normalizar nome do projeto para matching
                UPPER(TRIM(REPLACE(p.nome, '_', ''))) AS projeto_nome_normalizado,
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
                -- Incluir todos os projetos (removido filtro restritivo de jira_project_key)
                -- AND (p.id IS NULL OR p.jira_project_key ~ '^(SEG|SGI|DTIN|TIN|WTMT|WENSAS|WTDPE|WTDQUO|WTDDMF|WPDREAC|WTDNS)-')
            ORDER BY
                hdr.ano, hdr.mes;
        """
        )
        
        # Query para buscar horas apontadas por mês e projeto PAI (hierarquia Jira)
        apontamentos_sql = text(
            """
            SELECT
                EXTRACT(YEAR FROM a.data_apontamento) AS ano,
                EXTRACT(MONTH FROM a.data_apontamento) AS mes,
                -- Usar projeto pai quando disponível, senão usar projeto atual
                COALESCE(a.projeto_pai_id, a.projeto_id) AS projeto_id,
                -- Usar nome do projeto pai quando disponível, senão usar nome do projeto atual
                COALESCE(a.nome_projeto_pai, p.nome) AS projeto_nome,
                -- Normalizar nome do projeto (remover underscores, espaços extras, maiúsculas)
                UPPER(TRIM(REPLACE(COALESCE(a.nome_projeto_pai, p.nome), '_', ''))) AS projeto_nome_normalizado,
                SUM(a.horas_apontadas) AS horas_apontadas,
                -- Informações adicionais para debug
                COUNT(CASE WHEN a.jira_parent_key IS NOT NULL THEN 1 END) AS subtarefas_count,
                COUNT(CASE WHEN a.jira_parent_key IS NULL THEN 1 END) AS tarefas_principais_count
            FROM
                apontamento a
            LEFT JOIN
                projeto p ON a.projeto_id = p.id
            WHERE
                a.recurso_id = :recurso_id
                AND EXTRACT(YEAR FROM a.data_apontamento) = :ano
                AND EXTRACT(MONTH FROM a.data_apontamento) BETWEEN :mes_inicio AND :mes_fim
            GROUP BY
                EXTRACT(YEAR FROM a.data_apontamento),
                EXTRACT(MONTH FROM a.data_apontamento),
                COALESCE(a.projeto_pai_id, a.projeto_id),
                COALESCE(a.nome_projeto_pai, p.nome),
                UPPER(TRIM(REPLACE(COALESCE(a.nome_projeto_pai, p.nome), '_', '')))
            ORDER BY
                ano, mes, projeto_id;
        """
        )

        params = {"recurso_id": recurso_id, "ano": ano, "mes_inicio": mes_inicio, "mes_fim": mes_fim}
        db_result = (await db.execute(raw_sql, params)).mappings().all()
        logger.info(f"[RAW SQL RESULT] Resultado do banco: {len(db_result)} linhas")
        
        # Executar query de apontamentos
        apontamentos_result = (await db.execute(apontamentos_sql, params)).mappings().all()
        logger.info(f"[APONTAMENTOS RESULT] Resultado dos apontamentos: {len(apontamentos_result)} linhas")
        
        # Criar dicionário de horas apontadas por mês e projeto (usando nome normalizado para matching)
        horas_apontadas_por_mes_projeto_nome = defaultdict(lambda: defaultdict(float))
        horas_apontadas_por_mes = defaultdict(float)
        
        for row in apontamentos_result:
            mes_key = (int(row['ano']), int(row['mes']))
            projeto_id = row['projeto_id']
            projeto_nome = row['projeto_nome']
            projeto_nome_normalizado = row.get('projeto_nome_normalizado', '').strip()
            horas = float(row['horas_apontadas'] or 0)
            subtarefas_count = int(row.get('subtarefas_count', 0))
            tarefas_principais_count = int(row.get('tarefas_principais_count', 0))
            
            # Log detalhado para debug da hierarquia
            logger.info(f"[APONTAMENTO_HIERARQUIA] Mês: {mes_key}, Projeto ID: {projeto_id}, "
                       f"Nome: '{projeto_nome}', Normalizado: '{projeto_nome_normalizado}', "
                       f"Horas: {horas}, Subtarefas: {subtarefas_count}, Principais: {tarefas_principais_count}")
            
            # Agrupar por mês e NOME NORMALIZADO (não por ID) para matching correto
            if projeto_nome_normalizado:
                horas_apontadas_por_mes_projeto_nome[mes_key][projeto_nome_normalizado] += horas
            
            # Total por mês
            horas_apontadas_por_mes[mes_key] += horas

        # Estrutura para processar os dados (usando nome normalizado como chave)
        disponibilidade_por_mes = defaultdict(lambda: {
            "capacidade_rh": 0,
            "alocacoes_detalhadas": defaultdict(lambda: {"horas": 0.0, "nome": "", "projeto_id": None})
        })

        for row in db_result:
            mes_key = (row['ano'], row['mes'])
            disponibilidade_por_mes[mes_key]["capacidade_rh"] = float(row['capacidade_rh'] or 0)

            if row['projeto_id'] and row['horas_planejadas'] is not None:
                proj_id = row['projeto_id']
                projeto_nome = row['projeto_nome']
                projeto_nome_normalizado = row.get('projeto_nome_normalizado', '').strip()
                horas_planejadas = float(row['horas_planejadas'])
                
                # Log detalhado para debug do planejamento
                logger.info(f"[PLANEJAMENTO_PROJETO] Mês: {mes_key}, Projeto ID: {proj_id}, "
                           f"Nome: '{projeto_nome}', Normalizado: '{projeto_nome_normalizado}', "
                           f"Horas Planejadas: {horas_planejadas}")
                
                # Usar nome normalizado como chave para matching
                if projeto_nome_normalizado:
                    disponibilidade_por_mes[mes_key]["alocacoes_detalhadas"][projeto_nome_normalizado]["horas"] += horas_planejadas
                    disponibilidade_por_mes[mes_key]["alocacoes_detalhadas"][projeto_nome_normalizado]["nome"] = projeto_nome
                    disponibilidade_por_mes[mes_key]["alocacoes_detalhadas"][projeto_nome_normalizado]["projeto_id"] = proj_id

        # Monta a resposta final no formato do schema
        lista_mensal = []
        for (ano_mes, mes_data) in sorted(disponibilidade_por_mes.items()):
            ano_val, mes_val = ano_mes
            capacidade = mes_data['capacidade_rh']

            if capacidade == 0:
                continue

            detalhes_projeto = []
            for nome_normalizado, pdata in mes_data["alocacoes_detalhadas"].items():
                projeto_id = pdata["projeto_id"]
                projeto_nome = pdata["nome"]
                horas_planejadas = pdata["horas"]
                
                # Buscar horas apontadas usando matching por similaridade
                nomes_apontamentos_disponiveis = list(horas_apontadas_por_mes_projeto_nome[ano_mes].keys())
                nome_match = encontrar_melhor_match_nome(nome_normalizado, nomes_apontamentos_disponiveis, threshold=0.6)
                
                horas_apontadas = 0.0
                if nome_match:
                    horas_apontadas = horas_apontadas_por_mes_projeto_nome[ano_mes].get(nome_match, 0.0)
                    logger.info(f"[MATCHING_SUCESSO] Mês: {ano_mes}, Planejamento: '{nome_normalizado}' → "
                               f"Apontamento: '{nome_match}', Planejadas: {horas_planejadas}, Apontadas: {horas_apontadas}")
                else:
                    logger.warning(f"[MATCHING_FALHOU] Mês: {ano_mes}, Planejamento: '{nome_normalizado}', "
                                  f"Planejadas: {horas_planejadas}, Apontadas: 0.0 (sem match)")
                
                detalhes_projeto.append(DisponibilidadeProjetoDetalhe(
                    projeto=ProjetoInfo(id=projeto_id, nome=projeto_nome),
                    horas_planejadas=horas_planejadas,
                    horas_apontadas=horas_apontadas
                ))

            total_planejado = sum(p.horas_planejadas for p in detalhes_projeto)
            total_apontado = horas_apontadas_por_mes.get(ano_mes, 0.0)  # NOVO: buscar horas apontadas
            horas_livres = capacidade - total_planejado
            percentual_alocacao = f"{(total_planejado / capacidade * 100):.1f}%" if capacidade > 0 else "0.0%"

            lista_mensal.append(DisponibilidadeMensal(
                mes=mes_val,
                ano=ano_val,
                capacidade_rh=capacidade,
                total_horas_planejadas=total_planejado,
                total_horas_apontadas=total_apontado,  # NOVO CAMPO
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
