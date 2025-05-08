import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.main import api_router, jira_webhook_router
from app.core.config import settings
from app.db.session import engine, Base

# Criar tabelas no banco de dados
# Comentar esta linha após a primeira execução ou usar Alembic para migrações
Base.metadata.create_all(bind=engine)

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="API para o Sistema de Gestão de Projetos e Melhorias",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=settings.root_path,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(api_router)
app.include_router(jira_webhook_router)


@app.get("/")
def root():
    """Redirecionamento para a documentação."""
    return {"message": "API WEG Automação PMO - Acesse /docs para a documentação."}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)