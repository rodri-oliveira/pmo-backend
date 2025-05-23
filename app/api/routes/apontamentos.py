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
    import logging
    logger = logging.getLogger("app.api.routes.apontamentos")
    logger.info(f"[create_apontamento] Início - recurso_id={apontamento.recurso_id}, projeto_id={apontamento.projeto_id}, data_apontamento={apontamento.data_apontamento}, horas_apontadas={apontamento.horas_apontadas}, user_id={current_user.id}")
    service = ApontamentoHoraService(db)
    try:
        result = await service.create_manual(apontamento, current_user.id)
        logger.info(f"[create_apontamento] Sucesso - apontamento criado com id={getattr(result, 'id', None)}")
        return result
    except ValueError as e:
        logger.warning(f"[create_apontamento] ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[create_apontamento] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao criar apontamento: {str(e)}")


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
    """
    import logging
    logger = logging.getLogger("app.api.routes.apontamentos")
    logger.info(f"[list_apontamentos] Início - filtros: skip={skip}, limit={limit}, recurso_id={recurso_id}, projeto_id={projeto_id}, equipe_id={equipe_id}, secao_id={secao_id}, data_inicio={data_inicio}, data_fim={data_fim}, fonte_apontamento={fonte_apontamento}, jira_issue_key={jira_issue_key}, user_id={getattr(current_user, 'id', None)}")
    try:
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
        result = await service.list_with_filters(filtros, skip=skip, limit=limit)
        logger.info(f"[list_apontamentos] Sucesso - {len(result)} registros retornados")
        return result
    except Exception as e:
        logger.error(f"[list_apontamentos] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao listar apontamentos: {str(e)}")


@router.get("/agregacoes", response_model=List[ApontamentoAggregationSchema])
async def get_apontamentos_agregacoes(
    recurso_id: Optional[int] = None,
    projeto_id: Optional[int] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    agrupar_por_recurso: bool = False,
    agrupar_por_projeto: bool = False,
    agrupar_por_data: bool = False,
    agrupar_por_mes: bool = False,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Obtém agregações (soma de horas) dos apontamentos com opção de filtros.
    """
    import logging
    logger = logging.getLogger("app.api.routes.apontamentos")
    logger.info(f"[get_apontamentos_agregacoes] Início - filtros: recurso_id={recurso_id}, projeto_id={projeto_id}, equipe_id={equipe_id}, secao_id={secao_id}, data_inicio={data_inicio}, data_fim={data_fim}, agrupar_por_recurso={agrupar_por_recurso}, agrupar_por_projeto={agrupar_por_projeto}, agrupar_por_data={agrupar_por_data}, agrupar_por_mes={agrupar_por_mes}, user_id={getattr(current_user, 'id', None)}")
    try:
        from datetime import datetime, date
        def parse_date_field(v, nome):
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
        try:
            data_inicio_conv = parse_date_field(data_inicio)
            data_fim_conv = parse_date_field(data_fim)
            logging.info(f"[get_apontamentos_agregacoes] data_inicio={data_inicio} (convertido={data_inicio_conv}) tipo={type(data_inicio_conv)}")
            logging.info(f"[get_apontamentos_agregacoes] data_fim={data_fim} (convertido={data_fim_conv}) tipo={type(data_fim_conv)}")
        except Exception as e:
            logging.error(f"Erro ao converter datas: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Erro ao converter datas: {str(e)}")
        service = ApontamentoHoraService(db)
        filtros = ApontamentoFilterSchema(
            recurso_id=recurso_id,
            projeto_id=projeto_id,
            equipe_id=equipe_id,
            secao_id=secao_id,
            data_inicio=data_inicio_conv,
            data_fim=data_fim_conv
        )
        result = await service.get_agregacoes(
            filtros, 
            agrupar_por_recurso, 
            agrupar_por_projeto, 
            agrupar_por_data, 
            agrupar_por_mes
        )
        if not result:
            logger.info("[get_apontamentos_agregacoes] Nenhum apontamento encontrado para os filtros informados.")
            return []
        logger.info(f"[get_apontamentos_agregacoes] Sucesso - {len(result)} agregações retornadas")
        return result
    except Exception as e:
        logger.error(f"[get_apontamentos_agregacoes] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao obter agregações: {str(e)}")


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
    import logging
    logger = logging.getLogger("app.api.routes.apontamentos")
    service = ApontamentoHoraService(db)
    logger.info(f"[update_apontamento] Início - apontamento_id={apontamento_id}, payload={apontamento_update}")
    # Verificar se o apontamento existe
    apontamento = await service.get(apontamento_id)
    if not apontamento:
        logger.warning(f"[update_apontamento] Apontamento {apontamento_id} não encontrado")
        raise HTTPException(status_code=404, detail=f"Apontamento {apontamento_id} não encontrado")
    # Verificar se é um apontamento manual (apenas estes podem ser editados)
    if apontamento.fonte_apontamento != FonteApontamento.MANUAL:
        logger.warning(f"[update_apontamento] Apontamento {apontamento_id} não é MANUAL (fonte={apontamento.fonte_apontamento})")
        raise HTTPException(
            status_code=403,
            detail=f"Apenas apontamentos manuais podem ser editados. Este apontamento é do tipo {apontamento.fonte_apontamento}"
        )
    try:
        result = await service.update_manual(apontamento_id, apontamento_update)
        if result is None:
            logger.warning(f"[update_apontamento] update_manual retornou None para apontamento_id={apontamento_id}")
            raise HTTPException(status_code=404, detail=f"Apontamento {apontamento_id} não encontrado ou não é MANUAL")
        logger.info(f"[update_apontamento] Sucesso - apontamento atualizado id={apontamento_id}")
        return result
    except ValueError as e:
        logger.warning(f"[update_apontamento] ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[update_apontamento] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao atualizar apontamento: {str(e)}")


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
    if apontamento.fonte_apontamento != FonteApontamento.MANUAL:
        raise HTTPException(
            status_code=403, 
            detail=f"Apenas apontamentos manuais podem ser removidos. Este apontamento é do tipo {apontamento.fonte_apontamento}"
        )
    
    try:
        await service.delete_manual(apontamento_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))