from typing import List, Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin_user
from app.db.session import get_async_db
from app.repositories.apontamento_repository import ApontamentoRepository, equipe_projeto_association
from app.db.orm_models import FonteApontamento
from app.models.usuario import UsuarioInDB
from app.services.relatorio_service import RelatorioService
from app.utils.date_utils import parse_date_flex
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/horas-apontadas")
async def relatorio_horas_apontadas(
    recurso_id: Optional[int] = None,
    projeto_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
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
    repository = ApontamentoRepository(db)

    # Parsear datas de filtro
    data_inicio_date = parse_date_flex(data_inicio)
    data_fim_date = parse_date_flex(data_fim)

    # A nova função do repositório retorna uma lista de dicionários (mappings)
    resultados = await repository.find_with_filters_and_aggregate(
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
    
    # Calcular o total de horas a partir dos resultados agregados.
    # A consulta agregada pode retornar Decimal, então convertemos para float.
    total_horas = sum(float(item.get('horas') or 0) for item in resultados)

    return {
        "items": resultados,
        "total_horas": total_horas
    }


@router.get("/horas-por-projeto")
async def get_horas_por_projeto(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    secao_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    agrupar_por_mes: bool = Query(True, description="Opcional. Agrupa os resultados por mês. Padrão: True."),
    db: AsyncSession = Depends(get_async_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Obtém o relatório de horas apontadas, agrupando por projeto. O agrupamento por mês é opcional.

    - **data_inicio**: Data inicial (formato `YYYY-MM-DD` ou `DD/MM/YYYY`).
    - **data_fim**: Data final (formato `YYYY-MM-DD` ou `DD/MM/YYYY`).
    - **secao_id**: (Opcional) ID da seção para filtrar.
    - **equipe_id**: (Opcional) ID da equipe para filtrar.
    - **agrupar_por_mes**: (Opcional) `True` para agrupar por mês. Padrão: `True`.

    **Retorna**:
    - `items`: Lista com os dados agregados.
    - `total_horas`: Soma total de horas.
    """
    repo = ApontamentoRepository(db)
    try:
        data_inicio_date = parse_date_flex(data_inicio)
        data_fim_date = parse_date_flex(data_fim)

        dados = await repo.find_with_filters_and_aggregate(
            data_inicio=data_inicio_date,
            data_fim=data_fim_date,
            secao_id=secao_id,
            equipe_id=equipe_id,
            agrupar_por_projeto=True,
            agrupar_por_mes=agrupar_por_mes
        )
        
        total_horas = sum(float(item.get('horas') or 0) for item in dados)

        return {
            "items": dados,
            "total_horas": total_horas
        }
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de horas por projeto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao gerar relatório.")

@router.get("/horas-por-recurso")
async def get_horas_por_recurso(
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    secao_id: Optional[int] = Query(None),
    equipe_id: Optional[int] = Query(None),
    recurso_id: Optional[int] = Query(None),
    agrupar_por_projeto: bool = Query(True, description="Opcional. Agrupa os resultados por projeto. Padrão: True."),
    agrupar_por_mes: bool = Query(True, description="Opcional. Agrupa os resultados por mês. Padrão: True."),
    db: AsyncSession = Depends(get_async_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Obtém o relatório de horas apontadas, agrupando por recurso. O agrupamento por projeto e mês é opcional.

    - **data_inicio**: Data inicial (formato `YYYY-MM-DD` ou `DD/MM/YYYY`).
    - **data_fim**: Data final (formato `YYYY-MM-DD` ou `DD/MM/YYYY`).
    - **secao_id**: (Opcional) ID da seção para filtrar.
    - **equipe_id**: (Opcional) ID da equipe para filtrar.
    - **recurso_id**: (Opcional) ID do recurso para filtrar.
    - **agrupar_por_projeto**: (Opcional) `True` para agrupar por projeto. Padrão: `True`.
    - **agrupar_por_mes**: (Opcional) `True` para agrupar por mês. Padrão: `True`.

    **Retorna**:
    - `items`: Lista com os dados agregados.
    - `total_horas`: Soma total de horas.
    """
    repo = ApontamentoRepository(db)
    try:
        data_inicio_date = parse_date_flex(data_inicio)
        data_fim_date = parse_date_flex(data_fim)

        dados = await repo.find_with_filters_and_aggregate(
            data_inicio=data_inicio_date,
            data_fim=data_fim_date,
            secao_id=secao_id,
            equipe_id=equipe_id,
            recurso_id=recurso_id,
            agrupar_por_recurso=True,
            agrupar_por_projeto=agrupar_por_projeto,
            agrupar_por_mes=agrupar_por_mes,
        )
        
        total_horas = sum(float(item.get('horas') or 0) for item in dados)

        return {
            "items": dados,
            "total_horas": total_horas
        }
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de horas por recurso: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao gerar relatório.")

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
    equipe_id: Optional[int] = Query(None, description="ID da equipe para filtrar a disponibilidade"),
    secao_id: Optional[int] = Query(None, description="ID da seção para filtrar a disponibilidade"),
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
    - **equipe_id**: ID da equipe para filtrar a disponibilidade (opcional).
    - **secao_id**: ID da seção para filtrar a disponibilidade (opcional).
    """
    relatorio_service = RelatorioService(db)
    try:
        dados_disponibilidade = await relatorio_service.get_disponibilidade_recursos(
            ano=ano,
            mes=mes,
            recurso_id=recurso_id,
            equipe_id=equipe_id,
            secao_id=secao_id
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