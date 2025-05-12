import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware # Adicionado
from app.core.config import settings
from app.core.docs import custom_openapi # Se você estiver usando este import

# --- Adicione estas duas linhas --- #
from app.api.main import api_router
from app.api.routes import health
# --------------------------------- #
from fastapi.responses import RedirectResponse
from app.db.session import async_engine, Base

# Configuração para SQLAlchemy assíncrono
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

# Adicionar suporte para greenlet
from starlette.middleware.base import BaseHTTPMiddleware
import contextvars
import greenlet

# Middleware para garantir que o contexto greenlet seja preservado
class SQLAlchemyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Salva o contexto atual
        current_context = contextvars.copy_context()
        
        # Executa o próximo middleware/endpoint com o contexto preservado
        response = await call_next(request)
        return response

# Não criar tabelas automaticamente - usar Alembic para migrações
# Para criar tabelas com SQLAlchemy assíncrono, seria necessário um código como:
# async def create_tables():
#     async with async_engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
# asyncio.run(create_tables())

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="API para o Sistema de Gestão de Projetos e Melhorias",
    docs_url="/docs",  # Garante que /docs está disponível
    redoc_url="/redoc",
)

# Adicionar middleware para SQLAlchemy assíncrono
app.add_middleware(SQLAlchemyMiddleware)

# Adicionar middleware CORS aqui
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if settings.root_path is not None:
    app.root_path = settings.root_path

if settings.swagger_servers_list is not None:
    app.servers = list(map(lambda x: { "url": x }, settings.swagger_servers_list.split(",")))

app.include_router(api_router, prefix="/backend/v1")
app.include_router(health.router, prefix="/health")

@app.get("/")
def root():
    """Redireciona para a documentação da API."""
    return RedirectResponse(url="/docs")

# Se você estiver usando uvicorn para rodar diretamente deste arquivo (para desenvolvimento):
# if __name__ == "__main__":
# uvicorn.run(app, host="0.0.0.0", port=8000)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000,reload=True)
