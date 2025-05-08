import uvicorn
from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.session import SessionLocal

def init() -> None:
    """Inicializa o banco de dados com dados básicos."""
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()

def start() -> None:
    """Inicia o servidor."""
    print("Inicializando banco de dados...")
    init()
    
    print("Iniciando servidor...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start() 