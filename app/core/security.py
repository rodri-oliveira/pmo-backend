from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.repositories.usuario_repository import UsuarioRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/backend/v1/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera o hash de uma senha."""
    return pwd_context.hash(password)

def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT para autenticação.
    
    Args:
        subject: Sujeito do token (geralmente ID do usuário)
        expires_delta: Tempo de expiração opcional
        
    Returns:
        str: Token JWT codificado
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Valida o token JWT e retorna o usuário autenticado.
    
    Args:
        db: Sessão do banco de dados
        token: Token JWT
        
    Returns:
        Dict: Dados do usuário autenticado
    
    Raises:
        HTTPException: Se o token for inválido ou o usuário não for encontrado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    repository = UsuarioRepository(db)
    user = repository.get(int(user_id))
    
    if user is None or not user.ativo:
        raise credentials_exception
    
    # Atualizar último acesso
    repository.update_last_access(int(user_id))
    
    return {
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "role": user.role,
        "ativo": user.ativo
    }

def get_current_admin_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Verifica se o usuário atual é um administrador.
    
    Args:
        current_user: Usuário autenticado
        
    Returns:
        Dict: Usuário administrador
    
    Raises:
        HTTPException: Se o usuário não for um administrador
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso permitido apenas para administradores"
        )
    return current_user 