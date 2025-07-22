from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

from app.db.session import get_async_db
from app.services.planejamento_horas_service import PlanejamentoHorasService
from app.models.schemas import (
    HorasPlanejadasCreate,
    HorasPlanejadasUpdate,
    HorasPlanejadasResponse,
    HorasPlanejadasAgrupadoListResponse
)

# Configurar o router
router = APIRouter(
    prefix="/horas-planejadas",
    tags=["Horas Planejadas"],
    include_in_schema=True
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/", response_model=HorasPlanejadasResponse, status_code=status.HTTP_201_CREATED)
async def create_horas_planejadas(
    horas_planejadas: HorasPlanejadasCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Cria um novo planejamento de horas para uma alocação.
    
    Args:
        horas_planejadas: Dados do planejamento de horas
        db: Sessão do banco de dados
    
    Returns:
        HorasPlanejadasResponse: Dados do planejamento criado
    
    Raises:
        HTTPException: Se houver erro na criação
    """
    try:
        service = PlanejamentoHorasService(db)
        result = await service.create_or_update_planejamento(
            alocacao_id=horas_planejadas.alocacao_id,
            ano=horas_planejadas.ano,
            mes=horas_planejadas.mes,
            horas_planejadas=horas_planejadas.horas_planejadas
        )
        
        logger.info(f"[create_horas_planejadas] Criado planejamento ID={result.get('id')} para alocação {horas_planejadas.alocacao_id}")
        
        return HorasPlanejadasResponse(
            id=result["id"],
            alocacao_id=result["alocacao_id"],
            ano=result["ano"],
            mes=result["mes"],
            horas_planejadas=result["horas_planejadas"],
            data_criacao=result["data_criacao"].isoformat(),
            data_atualizacao=result["data_atualizacao"].isoformat()
        )
        
    except ValueError as e:
        logger.warning(f"[create_horas_planejadas] Erro de validação: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e:
        logger.error(f"[create_horas_planejadas] Erro de integridade: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um planejamento para esta alocação, ano e mês"
        )
    except Exception as e:
        logger.error(f"[create_horas_planejadas] Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao criar planejamento"
        )

@router.get("/", response_model=HorasPlanejadasAgrupadoListResponse, summary="Listar Horas Planejadas com Paginação e Filtros")
async def list_horas_planejadas(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(10, ge=1, le=1000, description="Quantidade máxima de registros"),
    alocacao_id: Optional[int] = Query(None, gt=0, description="Filtrar por ID da alocação"),
    ano: Optional[int] = Query(None, ge=2020, le=2050, description="Filtrar por ano"),
    mes: Optional[int] = Query(None, ge=1, le=12, description="Filtrar por mês"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Lista planejamentos de horas com filtros opcionais.
    
    Args:
        skip: Número de registros a pular
        limit: Quantidade máxima de registros
        alocacao_id: Filtrar por ID da alocação
        ano: Filtrar por ano
        mes: Filtrar por mês
        db: Sessão do banco de dados
    
    Returns:
        HorasPlanejadasListResponse: Lista paginada de planejamentos
    """
    try:
        service = PlanejamentoHorasService(db)
        
        # Usar o método list_all que já retorna as alocações com horas agrupadas
        items, total = await service.list_all(skip, limit, alocacao_id, ano, mes)
        
        logger.info(f"[list_horas_planejadas] Retornando {len(items)} de {total} registros")
        
        # A estrutura retornada está de acordo com HorasPlanejadasAgrupadoResponse
        return HorasPlanejadasAgrupadoListResponse(total=total, items=items)
    except Exception as e:
        logger.error(f"[list_horas_planejadas] Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao listar planejamentos"
        )


# ------------------- Update por chave composta -------------------
@router.put(
    "/{alocacao_id}/{ano}/{mes}",
    response_model=HorasPlanejadasResponse,
    summary="Atualizar Horas Planejadas (alocacao_id/ano/mes)"
)
async def update_horas_planejadas(
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    ano: int = Path(..., ge=2020, le=2050, description="Ano"),
    mes: int = Path(..., ge=1, le=12, description="Mês"),
    payload: HorasPlanejadasUpdate = ...,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        service = PlanejamentoHorasService(db)
        result = await service.create_or_update_planejamento(
            alocacao_id=alocacao_id,
            ano=ano,
            mes=mes,
            horas_planejadas=payload.horas_planejadas
        )
        logger.info(
            f"[update_horas_planejadas] Planejamento atualizado para alocacao_id={alocacao_id}, ano={ano}, mes={mes}"
        )
        return HorasPlanejadasResponse(
            id=result["id"],
            alocacao_id=alocacao_id,
            ano=ano,
            mes=mes,
            horas_planejadas=payload.horas_planejadas,
            data_criacao=result["data_criacao"].isoformat() if "data_criacao" in result else "",
            data_atualizacao=result["data_atualizacao"].isoformat() if "data_atualizacao" in result else ""
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"[update_horas_planejadas] Erro inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar planejamento")


# ------------------- Delete por chave composta -------------------
@router.delete(
    "/{alocacao_id}/{ano}/{mes}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar Horas Planejadas (alocacao_id/ano/mes)"
)
async def delete_horas_planejadas(
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    ano: int = Path(..., ge=2020, le=2050, description="Ano"),
    mes: int = Path(..., ge=1, le=12, description="Mês"),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        service = PlanejamentoHorasService(db)
        await service.delete_planejamento_by_key(alocacao_id, ano, mes)
        logger.info(
            f"[delete_horas_planejadas] Planejamento removido: alocacao_id={alocacao_id}, ano={ano}, mes={mes}"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"[delete_horas_planejadas] Erro inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao deletar planejamento")
        
    except Exception as e:
        logger.error(f"[list_horas_planejadas] Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao listar planejamentos"
        )

@router.get("/{planejamento_id}", response_model=HorasPlanejadasResponse)
async def get_horas_planejadas(
    planejamento_id: int = Path(..., gt=0, description="ID do planejamento"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtém um planejamento de horas pelo ID.
    
    Args:
        planejamento_id: ID do planejamento
        db: Sessão do banco de dados
    
    Returns:
        HorasPlanejadasResponse: Dados do planejamento
    
    Raises:
        HTTPException: Se o planejamento não for encontrado
    """
    try:
        service = PlanejamentoHorasService(db)
        
        # TODO: Implementar método get_by_id no service
        # Por enquanto, vamos usar uma abordagem alternativa
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Endpoint em desenvolvimento - use filtro por alocacao_id na listagem"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[get_horas_planejadas] Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao buscar planejamento"
        )

@router.put("/{planejamento_id}", response_model=HorasPlanejadasResponse)
async def update_horas_planejadas(
    planejamento_update: HorasPlanejadasUpdate,
    planejamento_id: int = Path(..., gt=0, description="ID do planejamento"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Atualiza um planejamento de horas existente.
    
    Args:
        planejamento_update: Dados para atualização
        planejamento_id: ID do planejamento
        db: Sessão do banco de dados
    
    Returns:
        HorasPlanejadasResponse: Dados do planejamento atualizado
    
    Raises:
        HTTPException: Se o planejamento não for encontrado
    """
    try:
        # TODO: Implementar método update_by_id no service
        # Por enquanto, retornar não implementado
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Endpoint em desenvolvimento - use create_or_update via POST"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[update_horas_planejadas] Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao atualizar planejamento"
        )

@router.delete("/{planejamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_horas_planejadas(
    planejamento_id: int = Path(..., gt=0, description="ID do planejamento"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Remove um planejamento de horas.
    
    Args:
        planejamento_id: ID do planejamento
        db: Sessão do banco de dados
    
    Raises:
        HTTPException: Se o planejamento não for encontrado
    """
    try:
        # TODO: Implementar método delete_by_id no service
        # Por enquanto, retornar não implementado
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Endpoint em desenvolvimento"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[delete_horas_planejadas] Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao deletar planejamento"
        )

# Endpoints específicos úteis
@router.get("/alocacao/{alocacao_id}", response_model=List[HorasPlanejadasResponse])
async def get_horas_planejadas_by_alocacao(
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtém todos os planejamentos de horas de uma alocação.
    
    Args:
        alocacao_id: ID da alocação
        db: Sessão do banco de dados
    
    Returns:
        List[HorasPlanejadasResponse]: Lista de planejamentos da alocação
    """
    try:
        service = PlanejamentoHorasService(db)
        planejamentos = await service.list_by_alocacao(alocacao_id)
        
        logger.info(f"[get_horas_planejadas_by_alocacao] Encontrados {len(planejamentos)} planejamentos para alocação {alocacao_id}")
        
        return [
            HorasPlanejadasResponse(
                id=item["id"],
                alocacao_id=item["alocacao_id"],
                ano=item["ano"],
                mes=item["mes"],
                horas_planejadas=item["horas_planejadas"],
                data_criacao=item["data_criacao"].isoformat(),
                data_atualizacao=item["data_atualizacao"].isoformat()
            )
            for item in planejamentos
        ]
        
    except Exception as e:
        logger.error(f"[get_horas_planejadas_by_alocacao] Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao buscar planejamentos da alocação"
        )

@router.get("/periodo/{ano}/{mes}", response_model=List[HorasPlanejadasResponse])
async def get_horas_planejadas_by_periodo(
    ano: int = Path(..., ge=2020, le=2050, description="Ano"),
    mes: int = Path(..., ge=1, le=12, description="Mês"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtém todos os planejamentos de horas de um período específico.
    
    Args:
        ano: Ano
        mes: Mês
        db: Sessão do banco de dados
    
    Returns:
        List[HorasPlanejadasResponse]: Lista de planejamentos do período
    """
    try:
        # TODO: Implementar método list_by_periodo no service
        # Por enquanto, retornar não implementado
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Endpoint em desenvolvimento"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[get_horas_planejadas_by_periodo] Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao buscar planejamentos do período"
        )
