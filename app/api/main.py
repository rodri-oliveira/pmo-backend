from fastapi import APIRouter

from app.api.routes import (
    health, 
    secoes, 
    equipes, 
    recursos, 
    status_projetos,
    projetos, 
    alocacoes,
    planejamento_horas,
    horas_disponiveis,
    apontamentos, 
    usuarios,
    configuracoes,
    logs_atividade,
    sincronizacoes_jira,
    relatorios,
    jira_webhook
)

# Router principal com prefixo base da API
api_router = APIRouter(prefix="/backend/v1")

# Registrar os routers das entidades
api_router.include_router(health.router)
api_router.include_router(secoes.router)
api_router.include_router(equipes.router)
api_router.include_router(recursos.router)
api_router.include_router(status_projetos.router)
api_router.include_router(projetos.router)
api_router.include_router(alocacoes.router)
api_router.include_router(planejamento_horas.router)
api_router.include_router(horas_disponiveis.router)
api_router.include_router(apontamentos.router)
api_router.include_router(usuarios.router)
api_router.include_router(configuracoes.router)
api_router.include_router(logs_atividade.router)
api_router.include_router(sincronizacoes_jira.router)
api_router.include_router(relatorios.router)

# Outros routers serão adicionados aqui conforme o desenvolvimento
# api_router.include_router(equipes.router)
# api_router.include_router(projetos.router)
# api_router.include_router(status_projetos.router)
# etc.

# Router do webhook do Jira não tem o prefixo /backend/v1
jira_webhook_router = jira_webhook.router
