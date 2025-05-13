from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from app.api.dtos.auth_schema import Token, UserCreate, UserUpdate
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password, get_current_admin_user
from app.db.session import get_db
from app.repositories.usuario_repository import UsuarioRepository

router = APIRouter(tags=["Autenticação"])


@router.post("/auth/token", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Obtenha um token de acesso JWT para autenticação.
    
    Args:
        db: Sessão do banco de dados
        form_data: Dados do formulário de login (username=email, password)
        
    Returns:
        Token: Token de acesso JWT
    
    Raises:
        HTTPException: Se as credenciais forem inválidas
    """
    repository = UsuarioRepository(db)
    user = repository.get_by_email(form_data.username)
    
    if not user or not verify_password(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(user.id, expires_delta=access_token_expires),
        "token_type": "bearer",
    }


@router.post("/usuarios", response_model=Any)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    # Remova temporariamente a dependência de admin:
    # current_user: dict = Depends(get_current_admin_user),
) -> Any:
    """
    Cria um novo usuário (apenas admin).
    """
    repository = UsuarioRepository(db)
    # Verifique se já existe algum usuário cadastrado
    existing_users = db.query(Usuario).count()
    if existing_users > 0:
        # Se já existe, exija autenticação (adicione o parâmetro de volta depois)
        raise HTTPException(
            status_code=403,
            detail="Apenas administradores podem criar novos usuários"
        )

    existing_user = repository.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso",
        )
    user_dict = user_data.dict()
    user_dict["senha_hash"] = get_password_hash(user_data.password)
    del user_dict["password"]
    return repository.create(user_dict)