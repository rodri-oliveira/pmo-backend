from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Union
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.usuario import UsuarioBase, UsuarioInDB, TokenData

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

def create_access_token(subject: Union[str, int], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT de acesso.
    
    Args:
        subject: Identificador do usuário (username)
        expires_delta: Tempo de expiração do token
        
    Returns:
        Token JWT codificado
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Criar payload com 'sub' (subject) e 'exp' (expiration time)
    to_encode = {"sub": str(subject), "exp": expire}
    
    # Codificar o token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
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
    logging.info(f"get_current_user foi chamado com token: {token[:10] if token else 'None'}...")
    
    if not token:
        logging.error("Token não fornecido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        logging.info("Tentando decodificar o token JWT")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logging.info(f"Payload decodificado: {payload}")
        username: str = payload.get("sub")
        
        if username is None:
            logging.error("Token JWT não contém 'sub' (username)")
            raise credentials_exception
            
        token_data = TokenData(username=username)
        logging.info(f"Token decodificado com sucesso para o usuário: {username}")
        
    except JWTError as e:
        logging.error(f"Erro ao decodificar o token JWT: {str(e)}")
        raise credentials_exception
        
    logging.info(f"Buscando usuário {username} no banco de dados")
    from app.repositories.usuario_repository import UsuarioRepository
    usuario_repo = UsuarioRepository(db)
    usuario = await usuario_repo.get_by_username(username)
    
    if usuario is None:
        logging.error(f"Usuário {username} não encontrado no banco de dados")
        raise credentials_exception
        
    logging.info(f"Usuário {username} encontrado com sucesso")
    
    # Atualizar último acesso
    try:
        logging.info(f"Atualizando último acesso do usuário {username}")
        await usuario_repo.update_last_access(usuario.id)
    except Exception as e:
        logging.warning(f"Erro ao atualizar último acesso: {str(e)}")
    
    return usuario

async def get_current_admin_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
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
        current_user = await get_current_user(token, db)
        
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