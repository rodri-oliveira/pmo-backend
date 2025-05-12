from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dtos.apontamento_schema import (
    ApontamentoCreateSchema, 
    ApontamentoUpdateSchema, 
    ApontamentoResponseSchema,
    ApontamentoFilterSchema,
    ApontamentoAggregationSchema,
    FonteApontamento
)
from app.core.security import get_current_admin_user
from app.db.session import get_async_db
from app.services.apontamento_hora_service import ApontamentoHoraService

router = APIRouter(prefix="/apontamentos", tags=["Apontamentos"])


@router.post("/", response_model=ApontamentoResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_apontamento(
    apontamento: ApontamentoCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Cria um novo apontamento manual pelo Admin.
    
    Args:
        apontamento: Dados do apontamento a ser criado
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        ApontamentoResponseSchema: Dados do apontamento criado
    
    Raises:
        HTTPException: Se houver erro na criação
    """
    service = ApontamentoHoraService(db)
    try:
        # Passa o ID do admin atual para registrar quem criou o apontamento
        return await service.create_manual(apontamento, current_user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ApontamentoResponseSchema])
async def list_apontamentos(
    skip: int = 0,
    limit: int = 100,
    recurso_id: Optional[int] = None,
    projeto_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    fonte_apontamento: Optional[FonteApontamento] = None,
    jira_issue_key: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Lista apontamentos com opção de filtros avançados.
    
    Args:
        skip: Registros para pular (paginação)
        limit: Limite de registros (paginação)
        recurso_id: Filtro por ID do recurso
        projeto_id: Filtro por ID do projeto
        equipe_id: Filtro por ID da equipe do recurso
        secao_id: Filtro por ID da seção do recurso
        data_inicio: Filtro por data inicial
        data_fim: Filtro por data final
        fonte_apontamento: Filtro por fonte (MANUAL/JIRA)
        jira_issue_key: Filtro por chave de issue do Jira
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        List[ApontamentoResponseSchema]: Lista de apontamentos
    """
    service = ApontamentoHoraService(db)
    filtros = ApontamentoFilterSchema(
        recurso_id=recurso_id,
        projeto_id=projeto_id,
        equipe_id=equipe_id,
        secao_id=secao_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        fonte_apontamento=fonte_apontamento,
        jira_issue_key=jira_issue_key
    )
    return await service.list_with_filters(filtros, skip=skip, limit=limit)


@router.get("/agregacoes", response_model=List[ApontamentoAggregationSchema])
async def get_apontamentos_agregacoes(
    recurso_id: Optional[int] = None,
    projeto_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    agrupar_por_recurso: bool = False,
    agrupar_por_projeto: bool = False,
    agrupar_por_data: bool = False,
    agrupar_por_mes: bool = False,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Obtém agregações (soma de horas) dos apontamentos com opção de filtros.
    
    Args:
        recurso_id: Filtro por ID do recurso
        projeto_id: Filtro por ID do projeto
        equipe_id: Filtro por ID da equipe do recurso
        secao_id: Filtro por ID da seção do recurso
        data_inicio: Filtro por data inicial
        data_fim: Filtro por data final
        agrupar_por_recurso: Se deve agrupar por recurso
        agrupar_por_projeto: Se deve agrupar por projeto
        agrupar_por_data: Se deve agrupar por data
        agrupar_por_mes: Se deve agrupar por mês
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        List[ApontamentoAggregationSchema]: Lista de agregações
    """
    service = ApontamentoHoraService(db)
    filtros = ApontamentoFilterSchema(
        recurso_id=recurso_id,
        projeto_id=projeto_id,
        equipe_id=equipe_id,
        secao_id=secao_id,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    return await service.get_agregacoes(
        filtros, 
        agrupar_por_recurso, 
        agrupar_por_projeto, 
        agrupar_por_data, 
        agrupar_por_mes
    )


@router.get("/{apontamento_id}", response_model=ApontamentoResponseSchema)
async def get_apontamento(
    apontamento_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Obtém um apontamento pelo ID.
    
    Args:
        apontamento_id: ID do apontamento
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        ApontamentoResponseSchema: Dados do apontamento
    
    Raises:
        HTTPException: Se o apontamento não for encontrado
    """
    service = ApontamentoHoraService(db)
    apontamento = await service.get(apontamento_id)
    if not apontamento:
        raise HTTPException(status_code=404, detail=f"Apontamento {apontamento_id} não encontrado")
    return apontamento


@router.put("/{apontamento_id}", response_model=ApontamentoResponseSchema)
async def update_apontamento(
    apontamento_update: ApontamentoUpdateSchema,
    apontamento_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Atualiza um apontamento (apenas MANUAL).
    
    Args:
        apontamento_update: Dados para atualização
        apontamento_id: ID do apontamento
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        ApontamentoResponseSchema: Dados do apontamento atualizado
    
    Raises:
        HTTPException: 
            - 404: Se o apontamento não for encontrado
            - 403: Se o apontamento for do tipo JIRA (não editável)
            - 400: Para outros erros de validação
    """
    service = ApontamentoHoraService(db)
    
    # Verificar se o apontamento existe
    apontamento = await service.get(apontamento_id)
    if not apontamento:
        raise HTTPException(status_code=404, detail=f"Apontamento {apontamento_id} não encontrado")
    
    # Verificar se é um apontamento manual (apenas estes podem ser editados)
    if apontamento.fonte != FonteApontamento.MANUAL:
        raise HTTPException(
            status_code=403, 
            detail=f"Apenas apontamentos manuais podem ser editados. Este apontamento é do tipo {apontamento.fonte}"
        )
    
    try:
        return await service.update_manual(apontamento_id, apontamento_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{apontamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_apontamento(
    apontamento_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Remove um apontamento (apenas MANUAL).
    
    Args:
        apontamento_id: ID do apontamento
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Raises:
        HTTPException: 
            - 404: Se o apontamento não for encontrado
            - 403: Se o apontamento for do tipo JIRA (não removível)
            - 400: Para outros erros
    """
    service = ApontamentoHoraService(db)
    
    # Verificar se o apontamento existe
    apontamento = await service.get(apontamento_id)
    if not apontamento:
        raise HTTPException(status_code=404, detail=f"Apontamento {apontamento_id} não encontrado")
    
    # Verificar se é um apontamento manual (apenas estes podem ser removidos)
    if apontamento.fonte != FonteApontamento.MANUAL:
        raise HTTPException(
            status_code=403, 
            detail=f"Apenas apontamentos manuais podem ser removidos. Este apontamento é do tipo {apontamento.fonte}"
        )
    
    try:
        await service.delete_manual(apontamento_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))