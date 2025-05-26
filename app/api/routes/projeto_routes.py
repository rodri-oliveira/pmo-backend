from fastapi import APIRouter, HTTPException, Depends, Query
import logging
from starlette import status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dtos.projeto_schema import ProjetoCreateSchema
from app.application.dtos.projeto_dtos import ProjetoDTO, ProjetoCreateDTO, ProjetoUpdateDTO
from app.application.services.projeto_service import ProjetoService
from app.application.services.status_projeto_service import StatusProjetoService 
from app.infrastructure.repositories.sqlalchemy_projeto_repository import SQLAlchemyProjetoRepository
from app.infrastructure.repositories.sqlalchemy_status_projeto_repository import SQLAlchemyStatusProjetoRepository 
from app.db.session import get_async_db

router = APIRouter()

# Dependency for ProjetoService
async def get_projeto_service(db: AsyncSession = Depends(get_async_db)) -> ProjetoService:
    projeto_repository = SQLAlchemyProjetoRepository(db_session=db)
    status_projeto_repository = SQLAlchemyStatusProjetoRepository(db_session=db) 
    return ProjetoService(projeto_repository=projeto_repository, status_projeto_repository=status_projeto_repository)

@router.post("/", response_model=ProjetoDTO, status_code=status.HTTP_201_CREATED)
async def create_projeto(projeto_create: ProjetoCreateSchema, service: ProjetoService = Depends(get_projeto_service)):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info("[create_projeto] Início")
    try:
        result = await service.create_projeto(projeto_create)
        logger.info("[create_projeto] Sucesso")
        return result
    except HTTPException as e:
        logger.warning(f"[create_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[create_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao criar projeto: {str(e)}")

@router.get("/{projeto_id}", response_model=ProjetoDTO)
async def get_projeto(projeto_id: int, service: ProjetoService = Depends(get_projeto_service)):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info(f"[get_projeto] Início - projeto_id: {projeto_id}")
    try:
        projeto = await service.get_projeto_by_id(projeto_id)
        if projeto is None:
            logger.warning(f"[get_projeto] Projeto não encontrado - projeto_id: {projeto_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
        logger.info(f"[get_projeto] Sucesso - projeto_id: {projeto_id}")
        return projeto
    except HTTPException as e:
        logger.warning(f"[get_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[get_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao buscar projeto: {str(e)}")
    return projeto

@router.get("/", response_model=dict)
async def get_all_projetos(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    status_projeto: Optional[int] = None,
    service: ProjetoService = Depends(get_projeto_service)
):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info(f"[get_all_projetos] Início - skip={skip}, limit={limit}, status_projeto={status_projeto}")
    try:
        result = await service.get_all_projetos(skip=skip, limit=limit, status_projeto=status_projeto)
        logger.info(f"[get_all_projetos] Sucesso - {len(result)} registros retornados")
        return {"items": result}
    except HTTPException as e:
        logger.warning(f"[get_all_projetos] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[get_all_projetos] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao listar projetos: {str(e)}")

@router.put("/{projeto_id}", response_model=ProjetoDTO)
async def update_projeto(projeto_id: int, projeto_update: ProjetoUpdateDTO, service: ProjetoService = Depends(get_projeto_service)):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info(f"[update_projeto] Início - projeto_id: {projeto_id}")
    try:
        result = await service.update_projeto(projeto_id, projeto_update)
        logger.info(f"[update_projeto] Sucesso - projeto_id: {projeto_id}")
        return result
    except HTTPException as e:
        logger.warning(f"[update_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[update_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao atualizar projeto: {str(e)}")

@router.delete("/{projeto_id}", response_model=ProjetoDTO)
async def delete_projeto(projeto_id: int, service: ProjetoService = Depends(get_projeto_service)):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info(f"[delete_projeto] Início - projeto_id: {projeto_id}")
    try:
        result = await service.delete_projeto(projeto_id)
        logger.info(f"[delete_projeto] Sucesso - projeto_id: {projeto_id}")
        return result
    except HTTPException as e:
        logger.warning(f"[delete_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[delete_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao excluir projeto: {str(e)}")
