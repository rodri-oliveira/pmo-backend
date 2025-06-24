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

from sqlalchemy.future import select
from sqlalchemy import or_
from app.db.orm_models import Equipe
from app.core.security import get_current_admin_user

@router.get("/autocomplete", response_model=dict)
async def autocomplete_equipes(
    search: str = Query(..., min_length=1, description="Termo a ser buscado (nome da equipe)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    apenas_ativos: bool = Query(False),
    secao_id: int = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    query = select(Equipe).where(Equipe.nome.ilike(f"%{search}%"))
    if apenas_ativos:
        query = query.where(Equipe.ativo == True)
    if secao_id:
        query = query.where(Equipe.secao_id == secao_id)
    query = query.order_by(Equipe.nome.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    equipes = result.scalars().all()
    items = [{"id": e.id, "nome": e.nome} for e in equipes]
    return {"items": items}

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
    nome: Optional[str] = Query(default=None, description="Busca por nome da equipe"),
    limit: int = Query(default=100, ge=1, le=1000),
    apenas_ativos: bool = False,
    secao_id: Optional[int] = Query(default=None, description="Filtrar equipes por ID da seção"),
    db: AsyncSession = Depends(get_async_db)
):
    from sqlalchemy import func, or_
    # monta query
    base_query = select(Equipe)
    if nome:
        base_query = base_query.where(Equipe.nome.ilike(f"%{nome}%"))
    if secao_id is not None:
        base_query = base_query.where(Equipe.secao_id == secao_id)
    if apenas_ativos:
        base_query = base_query.where(Equipe.ativo == True)

    # total antes da paginação
    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # resultados
    if nome or secao_id is not None or apenas_ativos:
        result = await db.execute(base_query.order_by(Equipe.nome))
        equipes_full = result.scalars().all()
        equipes = equipes_full[skip: skip + limit]
    else:
        paginated = base_query.order_by(Equipe.nome).offset(skip).limit(limit)
        result = await db.execute(paginated)
        equipes = result.scalars().all()

    items = [EquipeDTO.model_validate(e) for e in equipes]
    return {"items": items, "total": total}


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
