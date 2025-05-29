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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/backend/v1/auth/token", auto_error=False)

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
    AUTENTICAÇÃO DESABILITADA - Retorna um usuário fictício para compatibilidade.
    (Logs detalhados adicionados para rastreamento de autenticação)
    """
    # Loga a chegada da requisição e o header Authorization (mascarando parte do token)
    if token:
        logging.info(f"[AUTH] Token recebido: {token[:8]}...{token[-8:]}")
    else:
        logging.warning("[AUTH] Token de autenticação NÃO encontrado na requisição!")
    
    # Loga o tipo de chamada (usuário fictício)
    logging.info("[AUTH] Autenticação desabilitada - retornando usuário fictício")
    
    # Retorna um usuário fictício para compatibilidade
    return UsuarioInDB(
        id=1,
        nome="Usuário Autenticado",
        email="usuario@weg.net",
        senha_hash="",
        ativo=True,
        is_admin=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

async def get_current_admin_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UsuarioInDB:
    """
    AUTENTICAÇÃO DESABILITADA - Retorna um usuário admin fictício para compatibilidade.
    (Logs detalhados adicionados para rastreamento de autenticação admin)
    """
    # Loga a chegada da requisição e o header Authorization (mascarando parte do token)
    if token:
        logging.info(f"[AUTH-ADMIN] Token recebido: {token[:8]}...{token[-8:]}")
    else:
        logging.warning("[AUTH-ADMIN] Token de autenticação NÃO encontrado na requisição!")
    
    # Loga o tipo de chamada (usuário admin fictício)
    logging.info("[AUTH-ADMIN] Autenticação de admin desabilitada - retornando usuário admin fictício")
    
    # Retorna um usuário admin fictício para compatibilidade
    return UsuarioInDB(
        id=1,
        nome="Admin",
        username="admin",
        perfil="admin",
        hashed_password="fakehashedpassword",
        email="admin@admin.com",
        is_active=True,
        is_superuser=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

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