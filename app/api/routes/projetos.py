from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.domain.models.projeto_model import Projeto
from app.application.dtos.projeto_dtos import ProjetoDTO, ProjetoComAlocacoesCreateDTO, ProjetoUpdateDTO
from app.application.services.projeto_service import ProjetoService
from app.infrastructure.repositories.sqlalchemy_projeto_repository import SQLAlchemyProjetoRepository
from app.infrastructure.repositories.sqlalchemy_status_projeto_repository import SQLAlchemyStatusProjetoRepository
from app.infrastructure.repositories.sqlalchemy_alocacao_repository import SQLAlchemyAlocacaoRepository
from app.infrastructure.repositories.sqlalchemy_horas_planejadas_repository import SQLAlchemyHorasPlanejadasRepository
from app.infrastructure.repositories.sqlalchemy_recurso_repository import SQLAlchemyRecursoRepository

# TODO: Substituir pela dependência de usuário autenticado quando implementado
async def get_current_user_mock():
    return {"username": "user_mock"}

router = APIRouter(prefix="/projetos", tags=["Projetos"])

class ProjetoResponse(BaseModel):
    items: List[ProjetoDTO]
    total: int

def get_projeto_service(db: AsyncSession = Depends(get_async_db)) -> ProjetoService:
    return ProjetoService(
        projeto_repository=SQLAlchemyProjetoRepository(db),
        status_projeto_repository=SQLAlchemyStatusProjetoRepository(db),
        alocacao_repository=SQLAlchemyAlocacaoRepository(db),
        horas_planejadas_repository=SQLAlchemyHorasPlanejadasRepository(db),
        recurso_repository=SQLAlchemyRecursoRepository(db)
    )

@router.get("/autocomplete", response_model=dict)
def autocomplete_projetos(
    search: str = Query(..., min_length=1, description="Termo a ser buscado (nome ou código da empresa)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(0, ge=0),
    apenas_ativos: bool = Query(False),
    status_projeto: int = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Endpoint para autocomplete de projetos por nome ou código da empresa.
    """
    query = db.query(Projeto)
    query = query.filter(Projeto.nome.ilike(f"%{search}%"))
    if apenas_ativos:
        query = query.filter(Projeto.ativo == True)
    if status_projeto:
        query = query.filter(Projeto.status_projeto_id == status_projeto)
    projetos = query.order_by(Projeto.nome.asc()).offset(skip).limit(limit).all()
    items = [
        {"id": p.id, "nome": p.nome}
        for p in projetos
    ]
    return {"items": items}


@router.post("/", response_model=ProjetoDTO, status_code=status.HTTP_201_CREATED)
async def create_projeto_with_allocations(
    data: ProjetoComAlocacoesCreateDTO,
    service: ProjetoService = Depends(get_projeto_service),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user_mock) # Substituir pela autenticação real
):
    try:
        return await service.create_projeto_com_alocacoes(data, db)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Idealmente, logar o erro aqui
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro inesperado: {e}")

@router.get("/", response_model=ProjetoResponse)
def list_projetos(
    skip: int = 0,
    limit: int = 100,
    nome: Optional[str] = None,
    codigo_empresa: Optional[str] = None,
    status_projeto: Optional[int] = None,
    ativo: Optional[bool] = None,
    equipe_id: Optional[int] = None,
    secao_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    service = ProjetoService(db)
    query = db.query(Projeto)
    if nome:
        query = query.filter(Projeto.nome.ilike(f"%{nome}%"))
    if codigo_empresa:
        query = query.filter(Projeto.codigo_empresa.ilike(f"%{codigo_empresa}%"))
    if status_projeto is not None:
        query = query.filter(Projeto.status_projeto_id == status_projeto)
    if ativo is not None:
        query = query.filter(Projeto.ativo == ativo)
    if equipe_id or secao_id:
        query = query.join(Recurso, Projeto.recurso_id == Recurso.id, isouter=False)
    if equipe_id:
        query = query.filter(Recurso.equipe_principal_id == equipe_id)
    if secao_id:
        query = query.join(Equipe, Recurso.equipe_principal_id == Equipe.id, isouter=False)
        query = query.filter(Equipe.secao_id == secao_id)

    total = query.count()
    projetos = query.offset(skip).limit(limit).all()
    return {"items": projetos, "total": total}

@router.get("/{projeto_id}", response_model=ProjetoResponseSchema)
def get_projeto(
    projeto_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    service = ProjetoService(db)
    projeto = service.get(projeto_id)
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return projeto

@router.put("/{projeto_id}", response_model=ProjetoResponseSchema)
def update_projeto(
    projeto_update: ProjetoUpdateSchema,
    projeto_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    service = ProjetoService(db)
    projeto = service.get(projeto_id)
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    try:
        return service.update(projeto_id, projeto_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{projeto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_projeto(
    projeto_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    service = ProjetoService(db)
    projeto = service.get(projeto_id)
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    try:
        service.delete(projeto_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))