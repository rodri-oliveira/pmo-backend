from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.usuario import UsuarioBase, UsuarioInDB

# Configuração de segurança
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/backend/v1/auth/token")

# Funções de segurança
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha informada corresponde ao hash armazenado."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera um hash seguro para a senha informada."""
    return pwd_context.hash(password)

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT de acesso.
    
    Args:
        data: Dados a serem codificados no token
        expires_delta: Tempo de expiração do token
        
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    expires = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expires})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> UsuarioInDB:
    """
    Obtém o usuário atual a partir do token JWT.
    
    Args:
        token: Token JWT de autenticação
        db: Sessão do banco de dados
        
    Returns:
        Usuário autenticado
        
    Raises:
        HTTPException: Se o token for inválido ou expirado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodifica o token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        # Busca o usuário no banco de dados
        from app.repositories.usuario_repository import UsuarioRepository
        usuario_repo = UsuarioRepository(db)
        usuario = usuario_repo.get_by_username(username)
        
        if usuario is None:
            raise credentials_exception
            
        return usuario
        
    except JWTError:
        raise credentials_exception

async def get_current_admin_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> dict:
    """
    Verifica se o usuário atual é administrador.
    
    Args:
        token: Token JWT
        db: Sessão do banco de dados
        
    Returns:
        dict: Dados do usuário administrador
        
    Raises:
        HTTPException: Se o usuário não for administrador
    """
    try:
        # Obter usuário autenticado
        current_user = get_current_user(token, db)
        
        # Verificar se é administrador
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissões de administrador necessárias",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return current_user
    except HTTPException as e:
        raise

# Função adicional para autenticação com WEG SSO (mock)
async def authenticate_with_weg_sso(token: str) -> Optional[UsuarioBase]:
    """
    Autentica um usuário através do SSO da WEG.
    
    Args:
        token: Token de autenticação SSO
        
    Returns:
        Dados do usuário autenticado ou None se a autenticação falhar
    """
    # Aqui seria implementada a lógica de verificação do token SSO com o sistema da WEG
    # Esta é uma implementação mock para demonstração
    
    # Em um cenário real, chamaríamos a API de autenticação da WEG
    # e receberíamos os dados do usuário
    
    return None  # Mock - implementação real seria feita conforme especificações da WEG 