from pydantic import BaseModel
from typing import Optional

class TokenData(BaseModel):
    """
    Modelo para os dados contidos no token JWT.
    """
    username: Optional[str] = None

class UsuarioBase(BaseModel):
    username: str
    email: str
    nome: str
    perfil: str
    ativo: bool = True

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    nome: Optional[str] = None
    perfil: Optional[str] = None
    ativo: Optional[bool] = None
    password: Optional[str] = None

class UsuarioInDB(UsuarioBase):
    id: int
    hashed_password: str

    class Config:
        from_attributes = True

class Usuario(UsuarioBase):
    id: int
    
    class Config:
        from_attributes = True 