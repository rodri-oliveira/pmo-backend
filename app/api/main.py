import logging
from fastapi import APIRouter

# Configura o logging para ser visível no uvicorn
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importação de todas as rotas da aplicação
from app.api.routes import (
    auth,
    secao_routes,
    equipe_routes,
    recurso_routes,
    status_projeto_routes,
    projeto_routes,
    planejamento_horas,
    apontamentos,
    filtros,
    relatorios,
    relatorios_dinamico,
    alocacao_routes,
    sincronizacoes_jira,
    dashboard
)

logger.info("Configurando o api_router principal...")

api_router = APIRouter()

# Registro de todas as rotas no router principal
api_router.include_router(auth.router, prefix="", tags=["Autenticação"])
api_router.include_router(secao_routes.router, prefix="/secoes", tags=["Seções"])
api_router.include_router(equipe_routes.router, prefix="/equipes", tags=["Equipes"])
api_router.include_router(recurso_routes.router, prefix="/recursos", tags=["Recursos"])
api_router.include_router(status_projeto_routes.router, prefix="/status-projetos", tags=["Status de Projetos"])
api_router.include_router(projeto_routes.router, prefix="/projetos", tags=["Projetos"])
api_router.include_router(alocacao_routes.router, tags=["Alocações"])
api_router.include_router(planejamento_horas.router, prefix="/planejamento-horas", tags=["Planejamento de Horas"])
api_router.include_router(apontamentos.router, prefix="/apontamentos", tags=["Apontamentos"])
api_router.include_router(filtros.router, prefix="/filtros", tags=["Filtros"])
api_router.include_router(relatorios.router, tags=["Relatórios"])
api_router.include_router(relatorios_dinamico.router)
api_router.include_router(sincronizacoes_jira.router, prefix="/sincronizacoes-jira", tags=["Integração Jira"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

logger.info("Todos os routers foram registrados com sucesso.")
