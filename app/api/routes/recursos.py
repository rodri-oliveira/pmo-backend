from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
import logging

from app.api.dtos.recurso_schema import RecursoCreateSchema, RecursoUpdateSchema, RecursoResponseSchema
from app.core.security import get_current_admin_user
from app.db.session import get_db
from app.services.recurso_service import RecursoService

router = APIRouter(prefix="/recursos", tags=["Recursos"])

@router.post("/", response_model=RecursoResponseSchema, status_code=status.HTTP_201_CREATED)
def create_recurso(
    recurso: RecursoCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    logger = logging.getLogger("app.api.routes.recursos")
    logger.info("[create_recurso] Início")
    service = RecursoService(db)
    try:
        result = service.create(recurso)
        logger.info("[create_recurso] Sucesso")
        return result
    except ValueError as e:
        logger.warning(f"[create_recurso] ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[create_recurso] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao criar recurso: {str(e)}")


@router.get("/", response_model=List[RecursoResponseSchema])
def list_recursos(
    skip: int = 0,
    limit: int = 100,
    nome: Optional[str] = None,
    email: Optional[str] = None,
    matricula: Optional[str] = None,
    equipe_id: Optional[int] = None,
    ativo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    logger = logging.getLogger("app.api.routes.recursos")
    logger.info(f"[list_recursos] Início - filtros: nome={nome}, email={email}, matricula={matricula}, equipe_id={equipe_id}, ativo={ativo}")
    service = RecursoService(db)
    try:
        result = service.list(
            skip=skip, 
            limit=limit, 
            nome=nome, 
            email=email, 
            matricula=matricula,
            equipe_id=equipe_id,
            ativo=ativo
        )
        logger.info(f"[list_recursos] Sucesso - {len(result)} registros retornados")
        return result
    except Exception as e:
        logger.error(f"[list_recursos] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao listar recursos: {str(e)}")


@router.get("/{recurso_id}", response_model=RecursoResponseSchema)
def get_recurso(
    recurso_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Obtém um recurso pelo ID.
    
    Args:
        recurso_id: ID do recurso
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        RecursoResponseSchema: Dados do recurso
    
    Raises:
        HTTPException: Se o recurso não for encontrado
    """
    service = RecursoService(db)
    recurso = service.get(recurso_id)
    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")
    return recurso


@router.put("/{recurso_id}", response_model=RecursoResponseSchema)
def update_recurso(
    recurso_update: RecursoUpdateSchema,
    recurso_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Atualiza um recurso.
    
    Args:
        recurso_update: Dados para atualização
        recurso_id: ID do recurso
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        RecursoResponseSchema: Dados do recurso atualizado
    
    Raises:
        HTTPException: Se o recurso não for encontrado ou houver erro na atualização
    """
    service = RecursoService(db)
    recurso = service.get(recurso_id)
    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")
    
    try:
        return service.update(recurso_id, recurso_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{recurso_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurso(
    recurso_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Remove um recurso (exclusão lógica - apenas marca como inativo).
    
    Args:
        recurso_id: ID do recurso
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Raises:
        HTTPException: Se o recurso não for encontrado ou não puder ser removido
    """
    service = RecursoService(db)
    recurso = service.get(recurso_id)
    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")
    
    try:
        service.delete(recurso_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 