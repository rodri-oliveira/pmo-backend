from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
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
    """
    Cria um novo projeto.
    
    Args:
        projeto: Dados do projeto a ser criado
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        ProjetoResponseSchema: Dados do projeto criado
    
    Raises:
        HTTPException: Se houver erro na criação
    """
    service = ProjetoService(db)
    try:
        return service.create(projeto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ProjetoResponseSchema])
def list_projetos(
    skip: int = 0,
    limit: int = 100,
    nome: Optional[str] = None,
    codigo_empresa: Optional[str] = None,
    status_projeto_id: Optional[int] = None,
    ativo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Lista projetos com opção de filtros.
    
    Args:
        skip: Registros para pular (paginação)
        limit: Limite de registros (paginação)
        nome: Filtro opcional por nome
        codigo_empresa: Filtro opcional por código da empresa
        status_projeto_id: Filtro opcional por status
        ativo: Filtro opcional por status ativo
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        List[ProjetoResponseSchema]: Lista de projetos
    """
    service = ProjetoService(db)
    return service.list(
        skip=skip, 
        limit=limit, 
        nome=nome, 
        codigo_empresa=codigo_empresa, 
        status_projeto_id=status_projeto_id, 
        ativo=ativo
    )


@router.get("/{projeto_id}", response_model=ProjetoResponseSchema)
def get_projeto(
    projeto_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Obtém um projeto pelo ID.
    
    Args:
        projeto_id: ID do projeto
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        ProjetoResponseSchema: Dados do projeto
    
    Raises:
        HTTPException: Se o projeto não for encontrado
    """
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
    """
    Atualiza um projeto.
    
    Args:
        projeto_update: Dados para atualização
        projeto_id: ID do projeto
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        ProjetoResponseSchema: Dados do projeto atualizado
    
    Raises:
        HTTPException: Se o projeto não for encontrado ou houver erro na atualização
    """
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
    """
    Remove um projeto (exclusão lógica - apenas marca como inativo).
    
    Args:
        projeto_id: ID do projeto
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Raises:
        HTTPException: Se o projeto não for encontrado ou não puder ser removido
    """
    service = ProjetoService(db)
    projeto = service.get(projeto_id)
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    try:
        service.delete(projeto_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 