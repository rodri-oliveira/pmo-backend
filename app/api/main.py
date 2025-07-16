import logging
from fastapi import APIRouter

# Configura o logging para ser visível no uvicorn
logger = logging.getLogger(__name__)

# Importação das rotas
from app.api.routes import (
    alocacao_routes,
    apontamentos,
    auth,
    equipe_routes,
    projeto_routes,
    recurso_routes,
    relatorios,
    secao_routes,
    status_projeto_routes,
    filtros,
    dashboard,
    matriz_planejamento,
    relatorios_dinamico,
    sincronizacoes_jira
)


logger.info("Configurando o api_router principal...")

api_router = APIRouter()

# Inclusão das rotas no roteador principal
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(secao_routes.router, prefix="/secoes", tags=["Seções"])
api_router.include_router(equipe_routes.router, prefix="/equipes", tags=["Equipes"])
api_router.include_router(recurso_routes.router, prefix="/recursos", tags=["Recursos"])
api_router.include_router(status_projeto_routes.router, prefix="/status-projeto", tags=["Status de Projeto"])
api_router.include_router(projeto_routes.router, prefix="/projetos", tags=["Projetos"])
api_router.include_router(alocacao_routes.router, prefix="/alocacoes", tags=["Alocações"])
api_router.include_router(apontamentos.router, prefix="/apontamentos", tags=["Apontamentos"])
api_router.include_router(filtros.router, prefix="/filtros", tags=["Filtros"])
api_router.include_router(relatorios.router, prefix="/relatorios", tags=["Relatórios"])
api_router.include_router(relatorios_dinamico.router, prefix="/relatorios-dinamico", tags=["Relatórios Dinâmicos"])
api_router.include_router(sincronizacoes_jira.router, prefix="/sincronizacoes-jira", tags=["Sincronizações Jira"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(matriz_planejamento.router, prefix="/matriz-planejamento", tags=["Matriz de Planejamento"])

logger.info("Todas as rotas foram incluídas no api_router.")
# Força o salvamento do arquivo para limpar o cache de importação
logger.info("Todos os routers foram registrados com sucesso.")
