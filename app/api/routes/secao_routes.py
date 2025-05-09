from fastapi import APIRouter, HTTPException, Depends, Query
from starlette import status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.secao_dtos import SecaoDTO, SecaoCreateDTO, SecaoUpdateDTO
from app.application.services.secao_service import SecaoService
from app.infrastructure.repositories.sqlalchemy_secao_repository import SQLAlchemySecaoRepository
from app.infrastructure.database.database_config import get_db

router = APIRouter()

# Dependency for SecaoService
async def get_secao_service(db: AsyncSession = Depends(get_db)) -> SecaoService:
    secao_repository = SQLAlchemySecaoRepository(db_session=db)
    return SecaoService(secao_repository=secao_repository)

@router.post("/", response_model=SecaoDTO, status_code=status.HTTP_201_CREATED)
async def create_secao(secao_create_dto: SecaoCreateDTO, service: SecaoService = Depends(get_secao_service)):
    try:
        return await service.create_secao(secao_create_dto)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{secao_id}", response_model=SecaoDTO)
async def get_secao(secao_id: int, service: SecaoService = Depends(get_secao_service)):
    secao = await service.get_secao_by_id(secao_id)
    if secao is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seção não encontrada")
    return secao

@router.get("/", response_model=List[SecaoDTO])
async def get_all_secoes(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=1000),
    apenas_ativos: bool = False,
    service: SecaoService = Depends(get_secao_service)
):
    return await service.get_all_secoes(skip=skip, limit=limit, apenas_ativos=apenas_ativos)

@router.put("/{secao_id}", response_model=SecaoDTO)
async def update_secao(secao_id: int, secao_update_dto: SecaoUpdateDTO, service: SecaoService = Depends(get_secao_service)):
    try:
        secao = await service.update_secao(secao_id, secao_update_dto)
        if secao is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seção não encontrada para atualização")
        return secao
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{secao_id}", response_model=SecaoDTO)
async def delete_secao(secao_id: int, service: SecaoService = Depends(get_secao_service)):
    secao = await service.delete_secao(secao_id)
    if secao is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seção não encontrada para exclusão")
    return secao

