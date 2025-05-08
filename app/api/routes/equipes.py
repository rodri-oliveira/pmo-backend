from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.api.dtos.equipe_schema import EquipeCreateSchema, EquipeUpdateSchema, EquipeResponseSchema
from app.core.security import get_current_admin_user
from app.db.session import get_db
from app.services.equipe_service import EquipeService

router = APIRouter(prefix="/equipes", tags=["Equipes"])


@router.post("/", response_model=EquipeResponseSchema, status_code=status.HTTP_201_CREATED)
def create_equipe(
    equipe: EquipeCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Cria uma nova equipe.
    
    Args:
        equipe: Dados da equipe a ser criada
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        EquipeResponseSchema: Dados da equipe criada
    
    Raises:
        HTTPException: Se houver erro na criação
    """
    service = EquipeService(db)
    try:
        return service.create(equipe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[EquipeResponseSchema])
def list_equipes(
    skip: int = 0,
    limit: int = 100,
    nome: Optional[str] = None,
    secao_id: Optional[int] = None,
    ativo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Lista equipes com opção de filtros.
    
    Args:
        skip: Registros para pular (paginação)
        limit: Limite de registros (paginação)
        nome: Filtro opcional por nome
        secao_id: Filtro opcional por seção
        ativo: Filtro opcional por status ativo
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        List[EquipeResponseSchema]: Lista de equipes
    """
    service = EquipeService(db)
    return service.list(skip=skip, limit=limit, nome=nome, secao_id=secao_id, ativo=ativo)


@router.get("/{equipe_id}", response_model=EquipeResponseSchema)
def get_equipe(
    equipe_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Obtém uma equipe pelo ID.
    
    Args:
        equipe_id: ID da equipe
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        EquipeResponseSchema: Dados da equipe
    
    Raises:
        HTTPException: Se a equipe não for encontrada
    """
    service = EquipeService(db)
    equipe = service.get(equipe_id)
    if not equipe:
        raise HTTPException(status_code=404, detail="Equipe não encontrada")
    return equipe


@router.put("/{equipe_id}", response_model=EquipeResponseSchema)
def update_equipe(
    equipe_update: EquipeUpdateSchema,
    equipe_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Atualiza uma equipe.
    
    Args:
        equipe_update: Dados para atualização
        equipe_id: ID da equipe
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        EquipeResponseSchema: Dados da equipe atualizada
    
    Raises:
        HTTPException: Se a equipe não for encontrada ou houver erro na atualização
    """
    service = EquipeService(db)
    equipe = service.get(equipe_id)
    if not equipe:
        raise HTTPException(status_code=404, detail="Equipe não encontrada")
    
    try:
        return service.update(equipe_id, equipe_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{equipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipe(
    equipe_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Remove uma equipe (exclusão lógica - apenas marca como inativo).
    
    Args:
        equipe_id: ID da equipe
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Raises:
        HTTPException: Se a equipe não for encontrada ou não puder ser removida
    """
    service = EquipeService(db)
    equipe = service.get(equipe_id)
    if not equipe:
        raise HTTPException(status_code=404, detail="Equipe não encontrada")
    
    try:
        service.delete(equipe_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 