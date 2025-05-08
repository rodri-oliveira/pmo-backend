from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import get_password_hash
from app.db import base  # noqa: F401
from app.db.orm_models import Usuario, UserRole

# Função para criar usuário administrador inicial
def create_first_admin(db: Session) -> None:
    # Verificar se já existe algum usuário
    user = db.query(Usuario).first()
    if not user:
        admin = Usuario(
            nome="Administrador",
            email="admin@example.com",
            senha_hash=get_password_hash("password"),
            role=UserRole.ADMIN,
            ativo=True
        )
        db.add(admin)
        db.commit()
        print("Usuário admin criado com sucesso!")

# Função para inicializar o banco com dados básicos
def init_db(db: Session) -> None:
    create_first_admin(db)
    print("Banco de dados inicializado com sucesso!") 