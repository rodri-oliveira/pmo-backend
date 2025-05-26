from fastapi import APIRouter, HTTPException, Depends, Query
from starlette import status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.equipe_dtos import EquipeDTO, EquipeCreateDTO, EquipeUpdateDTO
from app.application.services.equipe_service import EquipeService
from app.application.services.secao_service import SecaoService # For secao_repository dependency
from app.infrastructure.repositories.sqlalchemy_equipe_repository import SQLAlchemyEquipeRepository
from app.infrastructure.repositories.sqlalchemy_secao_repository import SQLAlchemySecaoRepository # For secao_repository dependency
from app.db.session import get_async_db

router = APIRouter()

# Dependency for EquipeService
async def get_equipe_service(db: AsyncSession = Depends(get_async_db)) -> EquipeService:
    equipe_repository = SQLAlchemyEquipeRepository(db_session=db)
    secao_repository = SQLAlchemySecaoRepository(db_session=db) # SecaoService needs this
    return EquipeService(equipe_repository=equipe_repository, secao_repository=secao_repository)

@router.post("/", response_model=EquipeDTO, status_code=status.HTTP_201_CREATED)
async def create_equipe(equipe_create_dto: EquipeCreateDTO, service: EquipeService = Depends(get_equipe_service)):
    try:
        return await service.create_equipe(equipe_create_dto)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{equipe_id}", response_model=EquipeDTO)
async def get_equipe(equipe_id: int, service: EquipeService = Depends(get_equipe_service)):
    equipe = await service.get_equipe_by_id(equipe_id)
    if equipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipe não encontrada")
    return equipe

@router.get("/", response_model=dict)
async def get_all_equipes(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=1000),
    apenas_ativos: bool = False,
    secao_id: Optional[int] = Query(default=None, description="Filtrar equipes por ID da seção"),
    service: EquipeService = Depends(get_equipe_service)
):
    if secao_id is not None:
        equipes = await service.get_equipes_by_secao_id(secao_id=secao_id, skip=skip, limit=limit, apenas_ativos=apenas_ativos)
    else:
        equipes = await service.get_all_equipes(skip=skip, limit=limit, apenas_ativos=apenas_ativos)
    return {"items": equipes}


@router.put("/{equipe_id}", response_model=EquipeDTO)
async def update_equipe(equipe_id: int, equipe_update_dto: EquipeUpdateDTO, service: EquipeService = Depends(get_equipe_service)):
    try:
        equipe = await service.update_equipe(equipe_id, equipe_update_dto)
        if equipe is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipe não encontrada para atualização")
        return equipe
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{equipe_id}", response_model=EquipeDTO)
async def delete_equipe(equipe_id: int, service: EquipeService = Depends(get_equipe_service)):
    equipe = await service.delete_equipe(equipe_id)
    if equipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipe não encontrada para exclusão")
    return equipe
