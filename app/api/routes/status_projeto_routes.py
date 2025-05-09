from fastapi import APIRouter, HTTPException, Depends, Query
from starlette import status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.status_projeto_dtos import StatusProjetoDTO, StatusProjetoCreateDTO, StatusProjetoUpdateDTO
from app.application.services.status_projeto_service import StatusProjetoService
from app.infrastructure.repositories.sqlalchemy_status_projeto_repository import SQLAlchemyStatusProjetoRepository
from app.infrastructure.database.database_config import get_db

router = APIRouter()

# Dependency for StatusProjetoService
async def get_status_projeto_service(db: AsyncSession = Depends(get_db)) -> StatusProjetoService:
    status_projeto_repository = SQLAlchemyStatusProjetoRepository(db_session=db)
    return StatusProjetoService(status_projeto_repository=status_projeto_repository)

@router.post("/", response_model=StatusProjetoDTO, status_code=status.HTTP_201_CREATED)
async def create_status_projeto(status_create_dto: StatusProjetoCreateDTO, service: StatusProjetoService = Depends(get_status_projeto_service)):
    try:
        return await service.create_status_projeto(status_create_dto)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{status_id}", response_model=StatusProjetoDTO)
async def get_status_projeto(status_id: int, service: StatusProjetoService = Depends(get_status_projeto_service)):
    status_projeto = await service.get_status_projeto_by_id(status_id)
    if status_projeto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de Projeto não encontrado")
    return status_projeto

@router.get("/", response_model=List[StatusProjetoDTO])
async def get_all_status_projeto(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=1000),
    service: StatusProjetoService = Depends(get_status_projeto_service)
):
    return await service.get_all_status_projeto(skip=skip, limit=limit)

@router.put("/{status_id}", response_model=StatusProjetoDTO)
async def update_status_projeto(status_id: int, status_update_dto: StatusProjetoUpdateDTO, service: StatusProjetoService = Depends(get_status_projeto_service)):
    try:
        status_projeto = await service.update_status_projeto(status_id, status_update_dto)
        if status_projeto is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de Projeto não encontrado para atualização")
        return status_projeto
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{status_id}", response_model=StatusProjetoDTO)
async def delete_status_projeto(status_id: int, service: StatusProjetoService = Depends(get_status_projeto_service)):
    status_projeto = await service.delete_status_projeto(status_id)
    if status_projeto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status de Projeto não encontrado para exclusão")
    return status_projeto

