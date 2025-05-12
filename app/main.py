import uvicorn
import asyncio
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.docs import custom_openapi

# Importar routers
from app.api.main import api_router
from app.api.routes import health

# Importar configuração do banco de dados
from app.db.session import async_engine, Base

# Configuração para SQLAlchemy assíncrono
from sqlalchemy.ext.asyncio import async_scoped_session, AsyncSession

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="API para o Sistema de Gestão de Projetos e Melhorias",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Adicionar middleware CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Configurar root_path se necessário
if settings.root_path is not None:
    app.root_path = settings.root_path

# Configurar servidores para Swagger
if settings.swagger_servers_list is not None:
    app.servers = list(map(lambda x: { "url": x }, settings.swagger_servers_list.split(",")))

# Incluir routers
app.include_router(api_router, prefix="/backend/v1")
app.include_router(health.router, prefix="/health")

@app.get("/")
def root():
    """Redireciona para a documentação da API."""
    return RedirectResponse(url="/docs")

# Executar a aplicação com uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        workers=1  # Usar apenas um worker para evitar problemas com greenlet
    )
