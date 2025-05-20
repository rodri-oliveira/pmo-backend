from fastapi import APIRouter
from app.api.routes import auth
# Importar cada módulo individualmente
from app.api.routes import secao_routes
from app.api.routes import equipe_routes
from app.api.routes import recurso_routes
from app.api.routes import status_projeto_routes
from app.api.routes import projeto_routes
from app.api.routes import planejamento_horas
from app.api.routes import apontamentos
from app.api.routes import relatorios
from app.api.routes import alocacao_routes # Adicionar importação para alocacao_routes
import logging
logging.basicConfig(level=logging.INFO)
logging.info("api_router está sendo configurado!")

api_router = APIRouter()
#api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(secao_routes.router, prefix="/secoes", tags=["Seções"])
api_router.include_router(equipe_routes.router, prefix="/equipes", tags=["Equipes"])
api_router.include_router(recurso_routes.router, prefix="/recursos", tags=["Recursos"])
api_router.include_router(status_projeto_routes.router, prefix="/status-projetos", tags=["Status de Projetos"])
api_router.include_router(projeto_routes.router, prefix="/projetos", tags=["Projetos"])
api_router.include_router(planejamento_horas.router, prefix="/planejamento-horas", tags=["Planejamento de Horas"])
api_router.include_router(apontamentos.router, prefix="/apontamentos", tags=["Apontamentos"])
api_router.include_router(relatorios.router, prefix="/relatorios", tags=["Relatórios"])
# Remover o prefixo para o router de alocações, já que ele já define internamente
api_router.include_router(alocacao_routes.router, tags=["Alocações"]) # Incluir a rota de alocações
api_router.include_router(auth.router, prefix="", tags=["Autenticação"])
