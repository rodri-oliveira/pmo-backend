from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.dtos.projeto_schema import ProjetoCreateSchema, ProjetoUpdateSchema, ProjetoResponseSchema
from app.core.security import get_current_admin_user
from app.db.session import get_db
from app.services.projeto_service import ProjetoService
from app.models import Projeto, Recurso, Equipe

router = APIRouter(prefix="/projetos", tags=["Projetos"])

@router.get("/autocomplete", response_model=dict)
def autocomplete_projetos(
    search: str = Query(..., min_length=1, description="Termo a ser buscado (nome ou código da empresa)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    apenas_ativos: bool = Query(False),
    status_projeto: int = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Endpoint para autocomplete de projetos por nome ou código da empresa.
    """
    query = db.query(Projeto)
    query = query.filter(or_(Projeto.nome.ilike(f"%{search}%"), Projeto.codigo_empresa.ilike(f"%{search}%")))
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


@router.post("/", response_model=ProjetoResponseSchema, status_code=status.HTTP_201_CREATED)
def create_projeto(
    projeto: ProjetoCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    service = ProjetoService(db)
    try:
        result = service.create(projeto)
        print("DEBUG RETORNO POST:", result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=dict)
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
    query = service.model.query
    if nome:
        query = query.filter(service.model.nome.ilike(f"%{nome}%"))
    if codigo_empresa:
        query = query.filter(service.model.codigo_empresa.ilike(f"%{codigo_empresa}%"))
    if status_projeto is not None:
        query = query.filter(service.model.status_projeto_id == status_projeto)
    if ativo is not None:
        query = query.filter(service.model.ativo == ativo)
    if equipe_id or secao_id:
        query = query.join(Recurso, service.model.recurso_id == Recurso.id, isouter=False)
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