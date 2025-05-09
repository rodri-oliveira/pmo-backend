from fastapi import APIRouter

from app.api.routes import items, secao_routes, equipe_routes, recurso_routes, status_projeto_routes, projeto_routes # Added projeto_routes

api_router = APIRouter()
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(secao_routes.router, prefix="/secoes", tags=["Seções"])
api_router.include_router(equipe_routes.router, prefix="/equipes", tags=["Equipes"])
api_router.include_router(recurso_routes.router, prefix="/recursos", tags=["Recursos"])
api_router.include_router(status_projeto_routes.router, prefix="/status-projetos", tags=["Status de Projetos"])
api_router.include_router(projeto_routes.router, prefix="/projetos", tags=["Projetos"]) # Added projeto_routes router
