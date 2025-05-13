from fastapi import APIRouter, HTTPException, Depends, Query
from starlette import status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

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
async def create_projeto(projeto_create_dto: ProjetoCreateDTO, service: ProjetoService = Depends(get_projeto_service)):
    try:
        return await service.create_projeto(projeto_create_dto)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{projeto_id}", response_model=ProjetoDTO)
async def get_projeto(projeto_id: int, service: ProjetoService = Depends(get_projeto_service)):
    projeto = await service.get_projeto_by_id(projeto_id)
    if projeto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
    return projeto

@router.get("/", response_model=List[ProjetoDTO])
async def get_all_projetos(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=1000),
    apenas_ativos: bool = False,
    status_projeto: Optional[int] = Query(default=None, description="Filtrar projetos por ID do status"),
    service: ProjetoService = Depends(get_projeto_service)
):
    return await service.get_all_projetos(skip=skip, limit=limit, apenas_ativos=apenas_ativos, status_projeto=status_projeto)

@router.put("/{projeto_id}", response_model=ProjetoDTO)
async def update_projeto(projeto_id: int, projeto_update_dto: ProjetoUpdateDTO, service: ProjetoService = Depends(get_projeto_service)):
    try:
        projeto = await service.update_projeto(projeto_id, projeto_update_dto)
        if projeto is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado para atualização")
        return projeto
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{projeto_id}", response_model=ProjetoDTO)
async def delete_projeto(projeto_id: int, service: ProjetoService = Depends(get_projeto_service)):
    projeto = await service.delete_projeto(projeto_id)
    if projeto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado para exclusão")
    return projeto
