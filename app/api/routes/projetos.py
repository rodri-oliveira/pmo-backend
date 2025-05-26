from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.dtos.projeto_schema import ProjetoCreateSchema, ProjetoUpdateSchema, ProjetoResponseSchema
from app.core.security import get_current_admin_user
from app.db.session import get_db
from app.services.projeto_service import ProjetoService

router = APIRouter(prefix="/projetos", tags=["Projetos"])

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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    service = ProjetoService(db)
    projetos = service.list(
        skip=skip, 
        limit=limit, 
        nome=nome, 
        codigo_empresa=codigo_empresa, 
        status_projeto=status_projeto, 
        ativo=ativo
    )
    return {"items": projetos}

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