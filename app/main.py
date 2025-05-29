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
import logging
import os
from datetime import datetime

# Configurar logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Configurar logs específicos
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)

# Configurar logs para integração com Jira
jira_logger = logging.getLogger("app.integrations.jira_client")
jira_logger.setLevel(logging.DEBUG)

logger.info("FastAPI principal está iniciando!")

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
    try:
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=8000,
            reload=True,
            workers=1  # Usar apenas um worker para evitar problemas com greenlet
        )
    except Exception as e:
        import traceback
        logging.error(f"Erro ao iniciar o servidor Uvicorn: {e}\n{traceback.format_exc()}")
        print(f"Erro ao iniciar o servidor Uvicorn: {e}\n{traceback.format_exc()}")
