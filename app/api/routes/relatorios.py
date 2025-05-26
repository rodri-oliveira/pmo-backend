from typing import List, Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin_user
from app.db.session import get_async_db
from app.repositories.apontamento_repository import ApontamentoRepository
from app.db.orm_models import FonteApontamento
from app.models.usuario import UsuarioInDB
from app.services.relatorio_service import RelatorioService

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/horas-apontadas")
async def relatorio_horas_apontadas(
    recurso_id: Optional[int] = None,
    projeto_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    data_inicio: Optional[str] = None,  # <-- Trocar aqui
    data_fim: Optional[str] = None,     # <-- Trocar aqui
    fonte_apontamento: Optional[FonteApontamento] = None,
    agrupar_por_recurso: bool = False,
    agrupar_por_projeto: bool = False,
    agrupar_por_data: bool = False,
    agrupar_por_mes: bool = True,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Gera relatório de horas apontadas com opções de filtro e agrupamento.
    
    Args:
        recurso_id: Filtro por ID do recurso
        projeto_id: Filtro por ID do projeto
        equipe_id: Filtro por ID da equipe
        secao_id: Filtro por ID da seção
        data_inicio: Filtro por data inicial
        data_fim: Filtro por data final
        fonte_apontamento: Filtro por fonte (JIRA/MANUAL)
        agrupar_por_recurso: Se deve agrupar por recurso
        agrupar_por_projeto: Se deve agrupar por projeto
        agrupar_por_data: Se deve agrupar por data
        agrupar_por_mes: Se deve agrupar por mês (default True)
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        List[Dict[str, Any]]: Relatório de horas apontadas
    """
    from datetime import datetime
    from datetime import datetime
    repository = ApontamentoRepository(db)

    def parse_date(value):
        if value is None:
            return None
        try:
            # Tenta formato ISO
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            try:
                # Tenta formato brasileiro
                return datetime.strptime(value, "%d/%m/%Y").date()
            except ValueError:
                raise HTTPException(status_code=422, detail=f"Formato de data inválido: {value}. Use YYYY-MM-DD ou DD/MM/YYYY.")

    data_inicio_date = parse_date(data_inicio)
    data_fim_date = parse_date(data_fim)

    def parse_date(value):
        if value is None:
            return None
        try:
            # Tenta formato ISO
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            try:
                # Tenta formato brasileiro
                return datetime.strptime(value, "%d/%m/%Y").date()
            except ValueError:
                raise HTTPException(status_code=422, detail=f"Formato de data inválido: {value}. Use YYYY-MM-DD ou DD/MM/YYYY.")

    data_inicio_date = parse_date(data_inicio)
    data_fim_date = parse_date(data_fim)

    return await repository.find_with_filters_and_aggregate(
        recurso_id=recurso_id,
        projeto_id=projeto_id,
        equipe_id=equipe_id,
        secao_id=secao_id,
        data_inicio=data_inicio_date,
        data_fim=data_fim_date,
        fonte_apontamento=fonte_apontamento,
        agrupar_por_recurso=agrupar_por_recurso,
        agrupar_por_projeto=agrupar_por_projeto,
        agrupar_por_data=agrupar_por_data,
        agrupar_por_mes=agrupar_por_mes
    )


@router.get("/comparativo-planejado-realizado", response_model=dict)
async def relatorio_comparativo(
    ano: int = Query(..., description="Ano do relatório"),
    mes: Optional[int] = Query(None, description="Mês do relatório (opcional)"),
    recurso_id: Optional[int] = None,
    projeto_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Gera relatório comparativo entre horas planejadas e apontadas.
    
    Args:
        ano: Ano do relatório
        mes: Mês do relatório (opcional)
        recurso_id: Filtro por ID do recurso
        projeto_id: Filtro por ID do projeto
        equipe_id: Filtro por ID da equipe
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        Dict[str, Any]: Relatório comparativo
    """
    # Aqui usaríamos uma query SQL mais complexa que junta dados de apontamento e planejamento
    # Simplificando para este exemplo
    sql = """
    SELECT 
        r.id as recurso_id,
        r.nome as recurso_nome,
        p.id as projeto_id,
        p.nome as projeto_nome,
        COALESCE(sum(hp.horas_planejadas), 0) as horas_planejadas,
        COALESCE(sum(a.horas_apontadas), 0) as horas_apontadas,
        COALESCE(sum(hp.horas_planejadas), 0) - COALESCE(sum(a.horas_apontadas), 0) as diferenca
    FROM 
        recurso r
    JOIN 
        alocacao_recurso_projeto arp ON r.id = arp.recurso_id
    JOIN 
        projeto p ON p.id = arp.projeto_id
    LEFT JOIN 
        horas_planejadas_alocacao hp ON hp.alocacao_id = arp.id 
            AND hp.ano = :ano 
            AND (CAST(:mes AS INTEGER) IS NULL OR hp.mes = CAST(:mes AS INTEGER))
    LEFT JOIN 
        apontamento a ON a.recurso_id = r.id 
            AND a.projeto_id = p.id 
            AND EXTRACT(YEAR FROM a.data_apontamento) = :ano 
            AND (CAST(:mes AS INTEGER) IS NULL OR EXTRACT(MONTH FROM a.data_apontamento) = CAST(:mes AS INTEGER))
    WHERE 
        (CAST(:recurso_id AS INTEGER) IS NULL OR r.id = CAST(:recurso_id AS INTEGER))
        AND (CAST(:projeto_id AS INTEGER) IS NULL OR p.id = CAST(:projeto_id AS INTEGER))
        AND (CAST(:equipe_id AS INTEGER) IS NULL OR r.equipe_principal_id = CAST(:equipe_id AS INTEGER))
    GROUP BY 
        r.id, r.nome, p.id, p.nome
    ORDER BY 
        r.nome, p.nome
    """
    
    # Executar a query SQL real e retornar os resultados do banco
    params = {
        "ano": ano,
        "mes": mes,
        "recurso_id": recurso_id,
        "projeto_id": projeto_id,
        "equipe_id": equipe_id,
    }
    from sqlalchemy import text
    result = await db.execute(text(sql), params)
    rows = result.fetchall()
    items = [
        {
            "recurso_id": row.recurso_id,
            "recurso_nome": row.recurso_nome,
            "projeto_id": row.projeto_id,
            "projeto_nome": row.projeto_nome,
            "horas_planejadas": float(row.horas_planejadas) if row.horas_planejadas is not None else 0,
            "horas_apontadas": float(row.horas_apontadas) if row.horas_apontadas is not None else 0,
            "diferenca": float(row.diferenca) if row.diferenca is not None else 0
        }
        for row in rows
    ]
    return {"items": items}


@router.get("/horas-por-projeto")
async def get_horas_por_projeto(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    secao_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Obter relatório de horas apontadas por projeto.
    
    - **data_inicio**: Data inicial do período de análise
    - **data_fim**: Data final do período de análise
    - **secao_id**: Filtrar por seção específica
    - **equipe_id**: Filtrar por equipe específica
    
    Retorna uma lista de projetos com o total de horas apontadas.
    """
    relatorio_service = RelatorioService(db)
    
    # Conversão dos formatos de data
    from datetime import datetime, date
    def parse_date_field(v):
        if v is None:
            return v
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00')).date()
            except Exception:
                pass
            try:
                return datetime.strptime(v, "%d/%m/%Y").date()
            except Exception:
                pass
        return v
    data_inicio_conv = parse_date_field(data_inicio)
    data_fim_conv = parse_date_field(data_fim)
    result = await relatorio_service.get_horas_por_projeto(
        data_inicio=data_inicio_conv,
        data_fim=data_fim_conv,
        secao_id=secao_id,
        equipe_id=equipe_id
    )
    return {"items": result}

@router.get("/horas-por-recurso")
async def get_horas_por_recurso(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    projeto_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Obter relatório de horas apontadas por recurso.
    
    - **data_inicio**: Data inicial do período de análise (formatos aceitos: YYYY-MM-DD, DD/MM/YYYY)
    - **data_fim**: Data final do período de análise (formatos aceitos: YYYY-MM-DD, DD/MM/YYYY)
    - **projeto_id**: Filtrar por projeto específico
    - **equipe_id**: Filtrar por equipe específica
    - **secao_id**: Filtrar por seção específica
    
    Retorna uma lista de recursos com o total de horas apontadas.
    """
    relatorio_service = RelatorioService(db)
    
    # Conversão dos formatos de data
    from datetime import datetime, date
    def parse_date_field(v):
        if v is None:
            return v
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00')).date()
            except Exception:
                pass
            try:
                return datetime.strptime(v, "%d/%m/%Y").date()
            except Exception:
                pass
        return v
    data_inicio_conv = parse_date_field(data_inicio)
    data_fim_conv = parse_date_field(data_fim)
    result = await relatorio_service.get_horas_por_recurso(
        data_inicio=data_inicio_conv,
        data_fim=data_fim_conv,
        projeto_id=projeto_id,
        equipe_id=equipe_id,
        secao_id=secao_id
    )
    return {"items": result}

@router.get("/planejado-vs-realizado")
async def get_planejado_vs_realizado(
    ano: int = Query(..., description="Ano de referência"),
    mes: Optional[int] = Query(None, description="Mês de referência (1-12)"),
    projeto_id: Optional[int] = None,
    recurso_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Obter relatório comparativo entre horas planejadas e realizadas.
    
    - **ano**: Ano de referência (obrigatório)
    - **mes**: Mês de referência (opcional)
    - **projeto_id**: Filtrar por projeto específico
    - **recurso_id**: Filtrar por recurso específico
    - **equipe_id**: Filtrar por equipe específica
    - **secao_id**: Filtrar por seção específica
    
    Retorna uma lista com comparativo entre horas planejadas e realizadas.
    """
    # Validar mês
    if mes is not None and (mes < 1 or mes > 12):
        raise HTTPException(status_code=400, detail="Mês deve estar entre 1 e 12")
    
    relatorio_service = RelatorioService(db)
    
    result = await relatorio_service.get_analise_planejado_vs_realizado(
        ano=ano,
        mes=mes,
        projeto_id=projeto_id,
        recurso_id=recurso_id,
        equipe_id=equipe_id,
        secao_id=secao_id
    )
    return {"items": result}

@router.get("/disponibilidade-recursos")
async def get_disponibilidade_recursos_endpoint(
    ano: int = Query(..., description="Ano de referência para a disponibilidade"),
    mes: Optional[int] = Query(None, description="Mês de referência (1-12). Se não informado, retorna para o ano todo.", ge=1, le=12),
    recurso_id: Optional[int] = Query(None, description="ID do recurso para filtrar a disponibilidade"),
    # Adicionar outros Query Params para filtros como equipe_id, secao_id se necessário
    db: AsyncSession = Depends(get_async_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user) # Protegendo o endpoint
):
    """
    Retorna um relatório detalhado sobre a disponibilidade dos recursos.

    Inclui horas disponíveis (cadastro RH), horas planejadas em projetos,
    horas efetivamente realizadas (apontamentos), horas livres, e percentuais
    de alocação e utilização.

    - **ano**: Ano para o qual o relatório de disponibilidade é gerado.
    - **mes**: Mês específico para filtrar o relatório (opcional).
    - **recurso_id**: ID do recurso para obter disponibilidade específica (opcional).
    """
    relatorio_service = RelatorioService(db)
    try:
        dados_disponibilidade = await relatorio_service.get_disponibilidade_recursos(
            ano=ano,
            mes=mes,
            recurso_id=recurso_id
        )
        if not dados_disponibilidade and (recurso_id or mes):
            # Se filtros específicos foram aplicados e nada foi encontrado, pode ser um 404
            # ou simplesmente não há dados para essa combinação específica.
            # Para este exemplo, retornamos uma lista vazia, mas poderia ser um 404 se apropriado.
            # Ex: if recurso_id and not any(d['recurso_id'] == recurso_id for d in dados_disponibilidade):
            # raise HTTPException(status_code=404, detail="Recurso não encontrado ou sem dados de disponibilidade para o período.")
            pass # Retorna lista vazia por padrão se filtros não encontrarem dados
            
        return {"items": dados_disponibilidade}
    except Exception as e:
        # Logar a exceção e retornar um erro genérico pode ser uma boa prática
        # import logging
        # logging.exception("Erro ao gerar relatório de disponibilidade")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o relatório: {str(e)}")