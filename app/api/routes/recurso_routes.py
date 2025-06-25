from fastapi import APIRouter, HTTPException, Depends, Query
from starlette import status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.recurso_dtos import RecursoDTO, RecursoCreateDTO, RecursoUpdateDTO
from app.application.services.recurso_service import RecursoService
from app.application.services.equipe_service import EquipeService # For equipe_repository dependency
from app.infrastructure.repositories.sqlalchemy_recurso_repository import SQLAlchemyRecursoRepository
from app.infrastructure.repositories.sqlalchemy_equipe_repository import SQLAlchemyEquipeRepository # For equipe_repository dependency
from app.db.session import get_async_db

router = APIRouter()

# Dependency for RecursoService
async def get_recurso_service(db: AsyncSession = Depends(get_async_db)) -> RecursoService:
    recurso_repository = SQLAlchemyRecursoRepository(db_session=db)
    equipe_repository = SQLAlchemyEquipeRepository(db_session=db) # RecursoService needs this
    return RecursoService(recurso_repository=recurso_repository, equipe_repository=equipe_repository)

@router.get("/autocomplete", response_model=dict)
async def autocomplete_recursos(
    search: str = Query(..., min_length=1, description="Termo a ser buscado (nome, email ou matrícula)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    apenas_ativos: bool = Query(False),
    equipe_id: Optional[int] = Query(None),
    secao_id: Optional[int] = Query(None),
    service: RecursoService = Depends(get_recurso_service)
):
    """
    Autocomplete de recursos por nome, email ou matrícula.
    """
    recursos = await service.autocomplete_recursos(
        search=search,
        skip=skip,
        limit=limit,
        apenas_ativos=apenas_ativos,
        equipe_id=equipe_id,
        secao_id=secao_id
    )
    # Retornar apenas campos essenciais
    items = [
        {"id": r.id, "nome": r.nome}
        for r in recursos
    ]
    return {"items": items}

# Dependency for RecursoService
async def get_recurso_service(db: AsyncSession = Depends(get_async_db)) -> RecursoService:
    recurso_repository = SQLAlchemyRecursoRepository(db_session=db)
    equipe_repository = SQLAlchemyEquipeRepository(db_session=db) # RecursoService needs this
    return RecursoService(recurso_repository=recurso_repository, equipe_repository=equipe_repository)

@router.post("/", response_model=RecursoDTO, status_code=status.HTTP_201_CREATED)
async def create_recurso(recurso_create_dto: RecursoCreateDTO, service: RecursoService = Depends(get_recurso_service)):
    try:
        return await service.create_recurso(recurso_create_dto)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{recurso_id}", response_model=RecursoDTO)
async def get_recurso(recurso_id: int, service: RecursoService = Depends(get_recurso_service)):
    recurso = await service.get_recurso_by_id(recurso_id)
    if recurso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso não encontrado")
    return recurso

@router.get("/", response_model=dict)
async def get_all_recursos(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=1000),
    apenas_ativos: bool = False,
    equipe_id: Optional[int] = Query(default=None, description="Filtrar recursos por ID da equipe principal"),
    secao_id: Optional[int] = Query(default=None, description="Filtrar recursos por ID da seção"),
    service: RecursoService = Depends(get_recurso_service)
):
    try:
        recursos = await service.get_all_recursos(skip=skip, limit=limit, apenas_ativos=apenas_ativos, equipe_id=equipe_id, secao_id=secao_id)
        return {"items": recursos}
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        print(f"Erro detalhado ao buscar recursos: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar recursos: {str(e)}")

@router.put("/{recurso_id}", response_model=RecursoDTO)
async def update_recurso(recurso_id: int, recurso_update_dto: RecursoUpdateDTO, service: RecursoService = Depends(get_recurso_service)):
    try:
        recurso = await service.update_recurso(recurso_id, recurso_update_dto)
        if recurso is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso não encontrado para atualização")
        return recurso
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{recurso_id}", response_model=RecursoDTO)
async def delete_recurso(recurso_id: int, service: RecursoService = Depends(get_recurso_service)):
    recurso = await service.delete_recurso(recurso_id)
    if recurso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso não encontrado para exclusão")
    return recurso
