from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.dtos.auth_schema import Token, UserCreate, UserUpdate
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password, get_current_admin_user
from app.db.session import get_async_db
from app.repositories.usuario_repository import UsuarioRepository
from app.models.usuario import Usuario
import logging
import jwt

router = APIRouter(tags=["Autenticação"])


@router.post("/auth/token", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_async_db), form_data: OAuth2PasswordRequestForm = Depends()
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
    logging.info(f"Tentativa de login para o usuário: {form_data.username}")
    repository = UsuarioRepository(db)
    user = await repository.get_by_email(form_data.username)
    
    if not user or not verify_password(form_data.password, user.senha_hash):
        logging.warning(f"Falha na autenticação para o usuário: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.ativo:
        logging.warning(f"Tentativa de login com usuário inativo: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Atualizar último acesso
    try:
        await repository.update_last_access(user.id)
    except Exception as e:
        logging.warning(f"Erro ao atualizar último acesso: {str(e)}")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=user.username, expires_delta=access_token_expires)
    logging.info(f"Login bem-sucedido para o usuário: {form_data.username}")
    logging.info(f"Token gerado: {token[:15]}...")
    
    # Verificar se o token pode ser decodificado corretamente
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logging.info(f"Token decodificado com sucesso. Payload: {payload}")
    except Exception as e:
        logging.error(f"Erro ao decodificar o token gerado: {str(e)}")
    
    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/usuarios", response_model=Any)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db),
    # Remova temporariamente a dependência de admin:
    # current_user: dict = Depends(get_current_admin_user),
) -> Any:
    """
    Cria um novo usuário (apenas admin).
    """
    repository = UsuarioRepository(db)
    # Verifique se já existe algum usuário cadastrado
    result = await db.execute(select(Usuario))
    existing_users = len(result.scalars().all())
    
    if existing_users > 0:
        # Se já existe, exija autenticação (adicione o parâmetro de volta depois)
        raise HTTPException(
            status_code=403,
            detail="Apenas administradores podem criar novos usuários"
        )

    existing_user = await repository.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso",
        )
    user_dict = user_data.dict()
    user_dict["senha_hash"] = get_password_hash(user_data.password)
    del user_dict["password"]
    return await repository.create(user_dict)