from typing import List, Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_admin_user
from app.db.session import get_db
from app.repositories.apontamento_repository import ApontamentoRepository
from app.db.orm_models import FonteApontamento
from app.models.usuario import UsuarioInDB
from app.services.relatorio_service import RelatorioService

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/horas-apontadas")
def relatorio_horas_apontadas(
    recurso_id: Optional[int] = None,
    projeto_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    fonte_apontamento: Optional[FonteApontamento] = None,
    agrupar_por_recurso: bool = False,
    agrupar_por_projeto: bool = False,
    agrupar_por_data: bool = False,
    agrupar_por_mes: bool = True,
    db: Session = Depends(get_db),
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
    
    return repository.find_with_filters_and_aggregate(
        recurso_id=recurso_id,
        projeto_id=projeto_id,
        equipe_id=equipe_id,
        secao_id=secao_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        fonte_apontamento=fonte_apontamento,
        agrupar_por_recurso=agrupar_por_recurso,
        agrupar_por_projeto=agrupar_por_projeto,
        agrupar_por_data=agrupar_por_data,
        agrupar_por_mes=agrupar_por_mes
    )


@router.get("/comparativo-planejado-realizado")
def relatorio_comparativo(
    ano: int = Query(..., description="Ano do relatório"),
    mes: Optional[int] = Query(None, description="Mês do relatório (opcional)"),
    recurso_id: Optional[int] = None,
    projeto_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    db: Session = Depends(get_db),
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
        List[Dict[str, Any]]: Relatório comparativo
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
            AND (:mes IS NULL OR hp.mes = :mes)
    LEFT JOIN 
        apontamento a ON a.recurso_id = r.id 
            AND a.projeto_id = p.id 
            AND EXTRACT(YEAR FROM a.data_apontamento) = :ano 
            AND (:mes IS NULL OR EXTRACT(MONTH FROM a.data_apontamento) = :mes)
    WHERE 
        (:recurso_id IS NULL OR r.id = :recurso_id)
        AND (:projeto_id IS NULL OR p.id = :projeto_id)
        AND (:equipe_id IS NULL OR r.equipe_principal_id = :equipe_id)
    GROUP BY 
        r.id, r.nome, p.id, p.nome
    ORDER BY 
        r.nome, p.nome
    """
    
    # Aqui executaríamos a query SQL e retornaríamos os resultados
    # Retorno simulado para este exemplo
    return [
        {
            "recurso_id": 1,
            "recurso_nome": "João Silva",
            "projeto_id": 1,
            "projeto_nome": "Projeto A",
            "horas_planejadas": 160.0,
            "horas_apontadas": 152.5,
            "diferenca": 7.5
        },
        # ... mais resultados
    ] 

@router.get("/horas-por-projeto")
def get_horas_por_projeto(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    secao_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    db: Session = Depends(get_db),
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
    
    return relatorio_service.get_horas_por_projeto(
        data_inicio=data_inicio,
        data_fim=data_fim,
        secao_id=secao_id,
        equipe_id=equipe_id
    )

@router.get("/horas-por-recurso")
def get_horas_por_recurso(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    projeto_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Obter relatório de horas apontadas por recurso.
    
    - **data_inicio**: Data inicial do período de análise
    - **data_fim**: Data final do período de análise
    - **projeto_id**: Filtrar por projeto específico
    - **equipe_id**: Filtrar por equipe específica
    - **secao_id**: Filtrar por seção específica
    
    Retorna uma lista de recursos com o total de horas apontadas.
    """
    relatorio_service = RelatorioService(db)
    
    return relatorio_service.get_horas_por_recurso(
        data_inicio=data_inicio,
        data_fim=data_fim,
        projeto_id=projeto_id,
        equipe_id=equipe_id,
        secao_id=secao_id
    )

@router.get("/planejado-vs-realizado")
def get_planejado_vs_realizado(
    ano: int = Query(..., description="Ano de referência"),
    mes: Optional[int] = Query(None, description="Mês de referência (1-12)"),
    projeto_id: Optional[int] = None,
    recurso_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    db: Session = Depends(get_db),
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
    
    return relatorio_service.get_analise_planejado_vs_realizado(
        ano=ano,
        mes=mes,
        projeto_id=projeto_id,
        recurso_id=recurso_id,
        equipe_id=equipe_id,
        secao_id=secao_id
    )

@router.get("/disponibilidade-recursos")
def get_disponibilidade_recursos(
    ano: int = Query(..., description="Ano de referência"),
    mes: Optional[int] = Query(None, description="Mês de referência (1-12)"),
    recurso_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Obter relatório de disponibilidade de recursos.
    
    - **ano**: Ano de referência (obrigatório)
    - **mes**: Mês de referência (opcional)
    - **recurso_id**: Filtrar por recurso específico
    - **equipe_id**: Filtrar por equipe específica
    - **secao_id**: Filtrar por seção específica
    
    Retorna uma lista com análise de disponibilidade, alocação e utilização dos recursos.
    """
    # Validar mês
    if mes is not None and (mes < 1 or mes > 12):
        raise HTTPException(status_code=400, detail="Mês deve estar entre 1 e 12")
    
    relatorio_service = RelatorioService(db)
    
    return relatorio_service.get_disponibilidade_recursos(
        ano=ano,
        mes=mes,
        recurso_id=recurso_id,
        equipe_id=equipe_id,
        secao_id=secao_id
    ) 