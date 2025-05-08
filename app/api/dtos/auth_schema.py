from typing import Optional
from pydantic import BaseModel, EmailStr, validator

from app.models.schemas import UserRole

class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    email: EmailStr
    nome: str
    role: UserRole
    recurso_id: Optional[int] = None
    ativo: bool = True

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('A senha deve ter pelo menos 8 caracteres')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nome: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    recurso_id: Optional[int] = None
    ativo: Optional[bool] = None
    
    @validator('password')
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('A senha deve ter pelo menos 8 caracteres')
        return v 