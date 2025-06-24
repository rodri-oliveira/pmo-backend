from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
import logging

from app.api.dtos.recurso_schema import RecursoCreateSchema, RecursoUpdateSchema, RecursoResponseSchema
from app.core.security import get_current_admin_user
from app.db.session import get_db
from app.application.services.recurso_service import RecursoService

router = APIRouter(prefix="/recursos", tags=["Recursos"])

from app.db.orm_models import Recurso
from app.repositories.recurso_repository import RecursoRepository
from app.utils.search_utils import apply_search_filter
from sqlalchemy.orm import Session

@router.get("/autocomplete", response_model=dict)
def autocomplete_recursos(
    search: str = Query(..., min_length=1, description="Termo a ser buscado (nome, email ou matrícula)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    apenas_ativos: bool = Query(False),
    equipe_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Endpoint para autocomplete de recursos por nome, email ou matrícula.
    """
    query = db.query(Recurso)
    fields = [Recurso.nome, Recurso.email, Recurso.matricula]
    query = apply_search_filter(query, Recurso, search, fields)
    if apenas_ativos:
        query = query.filter(Recurso.ativo == True)
    if equipe_id:
        query = query.filter(Recurso.equipe_principal_id == equipe_id)
    recursos = query.order_by(Recurso.nome.asc()).offset(skip).limit(limit).all()
    # Retornar apenas campos essenciais
    items = [
        {
            "id": r.id,
            "nome": r.nome,
            "email": r.email,
            "matricula": r.matricula,
            "cargo": r.cargo,
            "ativo": r.ativo
        }
        for r in recursos
    ]
    return {"items": items}


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


@router.get("/", response_model=dict)
def list_recursos(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    nome: Optional[str] = None,
    email: Optional[str] = None,
    matricula: Optional[str] = None,
    equipe_id: Optional[int] = None,
    ativo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    logger = logging.getLogger("app.api.routes.recursos")
    logger.info(
        f"[list_recursos] Início - filtros: search={search}, nome={nome}, email={email}, matricula={matricula}, "
        f"equipe_id={equipe_id}, ativo={ativo}, skip={skip}, limit={limit}"
    )

    try:
        query = db.query(Recurso)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Recurso.nome.ilike(search_pattern),
                    Recurso.email.ilike(search_pattern),
                    Recurso.matricula.ilike(search_pattern)
                )
            )
        if nome:
            query = query.filter(Recurso.nome.ilike(f"%{nome}%"))
        if email:
            query = query.filter(Recurso.email.ilike(f"%{email}%"))
        if matricula:
            query = query.filter(Recurso.matricula.ilike(f"%{matricula}%"))
        if equipe_id is not None:
            query = query.filter(Recurso.equipe_principal_id == equipe_id)
        if ativo is not None:
            query = query.filter(Recurso.ativo == ativo)

        total_query = query.count()

        # Quando filtros de busca são aplicados (search ou campos específicos), podemos precisar paginar em memória
        if search or nome or email or matricula or equipe_id is not None or ativo is not None:
            recursos_full = query.order_by(Recurso.nome.asc()).all()
            recursos = recursos_full[skip: skip + limit]
        else:
            recursos = (
                query.order_by(Recurso.nome.asc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        total = total_query

        logger.info(f"[list_recursos] Sucesso - {len(recursos)} registros retornados / total={total}")
        return {"items": recursos, "total": total}
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