from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.api.dtos.secao_schema import SecaoCreateSchema, SecaoUpdateSchema, SecaoResponseSchema
from app.core.security import get_current_admin_user
from app.db.session import get_db
from app.services.secao_service import SecaoService

router = APIRouter(prefix="/secoes", tags=["Seções"])


@router.post("/", response_model=SecaoResponseSchema, status_code=status.HTTP_201_CREATED)
def create_secao(
    secao: SecaoCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Cria uma nova seção.
    
    Args:
        secao: Dados da seção a ser criada
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        SecaoResponseSchema: Dados da seção criada
    
    Raises:
        HTTPException: Se houver erro na criação
    """
    service = SecaoService(db)
    try:
        return service.create(secao)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[SecaoResponseSchema])
def list_secoes(
    skip: int = 0,
    limit: int = 100,
    nome: Optional[str] = None,
    ativo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Lista seções com opção de filtros.
    
    Args:
        skip: Registros para pular (paginação)
        limit: Limite de registros (paginação)
        nome: Filtro opcional por nome
        ativo: Filtro opcional por status ativo
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        List[SecaoResponseSchema]: Lista de seções
    """
    service = SecaoService(db)
    return service.list(skip=skip, limit=limit, nome=nome, ativo=ativo)


@router.get("/{secao_id}", response_model=SecaoResponseSchema)
def get_secao(
    secao_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Obtém uma seção pelo ID.
    
    Args:
        secao_id: ID da seção
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        SecaoResponseSchema: Dados da seção
    
    Raises:
        HTTPException: Se a seção não for encontrada
    """
    service = SecaoService(db)
    secao = service.get(secao_id)
    if not secao:
        raise HTTPException(status_code=404, detail="Seção não encontrada")
    return secao


@router.put("/{secao_id}", response_model=SecaoResponseSchema)
def update_secao(
    secao_update: SecaoUpdateSchema,
    secao_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Atualiza uma seção.
    
    Args:
        secao_update: Dados para atualização
        secao_id: ID da seção
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        SecaoResponseSchema: Dados da seção atualizada
    
    Raises:
        HTTPException: Se a seção não for encontrada ou houver erro na atualização
    """
    service = SecaoService(db)
    secao = service.get(secao_id)
    if not secao:
        raise HTTPException(status_code=404, detail="Seção não encontrada")
    
    try:
        return service.update(secao_id, secao_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{secao_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_secao(
    secao_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Remove uma seção (exclusão lógica - apenas marca como inativo).
    
    Args:
        secao_id: ID da seção
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Raises:
        HTTPException: Se a seção não for encontrada ou não puder ser removida
    """
    service = SecaoService(db)
    secao = service.get(secao_id)
    if not secao:
        raise HTTPException(status_code=404, detail="Seção não encontrada")
    
    try:
        service.delete(secao_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 