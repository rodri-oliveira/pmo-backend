import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.docs import custom_openapi # Se você estiver usando este import

# --- Adicione estas duas linhas --- #
from app.api.main import api_router
from app.api.routes import health
# --------------------------------- #

from app.db.session import engine, Base # Se esta for sua configuração de DB

# Criar tabelas no banco de dados
# Comentar esta linha após a primeira execução ou usar Alembic para migrações
# Base.metadata.create_all(bind=engine) # Verifique se esta linha é do seu projeto atual ou do antigo

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="API para o Sistema de Gestão de Projetos e Melhorias",
    docs_url="/docs",  # Garante que /docs está disponível
    redoc_url="/redoc",
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
