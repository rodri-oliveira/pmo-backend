from fastapi import APIRouter, HTTPException, Depends, Query
import logging
from starlette import status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.status_projeto_dtos import StatusProjetoDTO, StatusProjetoCreateDTO, StatusProjetoUpdateDTO
from app.application.services.status_projeto_service import StatusProjetoService
from app.infrastructure.repositories.sqlalchemy_status_projeto_repository import SQLAlchemyStatusProjetoRepository
from app.db.session import get_async_db

router = APIRouter()

# Dependency for StatusProjetoService
async def get_status_projeto_service(db: AsyncSession = Depends(get_async_db)) -> StatusProjetoService:
    status_projeto_repository = SQLAlchemyStatusProjetoRepository(db_session=db)
    return StatusProjetoService(status_projeto_repository=status_projeto_repository)

@router.post("/", response_model=StatusProjetoDTO, status_code=status.HTTP_201_CREATED)
async def create_status_projeto(status_create_dto: StatusProjetoCreateDTO, service: StatusProjetoService = Depends(get_status_projeto_service)):
    logger = logging.getLogger("app.api.routes.status_projeto_routes")
    logger.info("[create_status_projeto] Início")
    try:
        status_projeto = await service.create_status_projeto(status_create_dto)
        logger.info("[create_status_projeto] Sucesso")
        return status_projeto
    except HTTPException as e:
        logger.warning(f"[create_status_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[create_status_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{status_id}", response_model=StatusProjetoDTO)
async def get_status_projeto(status_id: int, service: StatusProjetoService = Depends(get_status_projeto_service)):
    logger = logging.getLogger("app.api.routes.status_projeto_routes")
    logger.info(f"[get_status_projeto] Início: status_id={status_id}")
    try:
        status_projeto = await service.get_status_projeto_by_id(status_id)
        if status_projeto is None:
            logger.warning(f"[get_status_projeto] Não encontrado: status_id={status_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de Projeto não encontrado")
        logger.info(f"[get_status_projeto] Sucesso: status_id={status_id}")
        return status_projeto
    except HTTPException as e:
        logger.warning(f"[get_status_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[get_status_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=List[StatusProjetoDTO])
async def get_all_status_projeto(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=1000),
    service: StatusProjetoService = Depends(get_status_projeto_service)
):
    logger = logging.getLogger("app.api.routes.status_projeto_routes")
    logger.info("[get_all_status_projeto] Início")
    try:
        status_projeto_list = await service.get_all_status_projeto(skip=skip, limit=limit)
        logger.info("[get_all_status_projeto] Sucesso")
        return status_projeto_list
    except HTTPException as e:
        logger.warning(f"[get_all_status_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[get_all_status_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{status_id}", response_model=StatusProjetoDTO)
async def update_status_projeto(status_id: int, status_update_dto: StatusProjetoUpdateDTO, service: StatusProjetoService = Depends(get_status_projeto_service)):
    logger = logging.getLogger("app.api.routes.status_projeto_routes")
    logger.info(f"[update_status_projeto] Início: status_id={status_id}")
    try:
        status_projeto = await service.update_status_projeto(status_id, status_update_dto)
        if status_projeto is None:
            logger.warning(f"[update_status_projeto] Não encontrado: status_id={status_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de Projeto não encontrado para atualização")
        logger.info(f"[update_status_projeto] Sucesso: status_id={status_id}")
        return status_projeto
    except HTTPException as e:
        logger.warning(f"[update_status_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[update_status_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{status_id}", response_model=StatusProjetoDTO)
async def delete_status_projeto(status_id: int, service: StatusProjetoService = Depends(get_status_projeto_service)):
    logger = logging.getLogger("app.api.routes.status_projeto_routes")
    logger.info(f"[delete_status_projeto] Início: status_id={status_id}")
    try:
        status_projeto = await service.delete_status_projeto(status_id)
        if status_projeto is None:
            logger.warning(f"[delete_status_projeto] Não encontrado: status_id={status_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de Projeto não encontrado para exclusão")
        logger.info(f"[delete_status_projeto] Sucesso: status_id={status_id}")
        return status_projeto
    except HTTPException as e:
        logger.warning(f"[delete_status_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[delete_status_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de Projeto não encontrado para exclusão")
    return status_projeto
