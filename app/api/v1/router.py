from fastapi import APIRouter
from app.api.v1.endpoints import calendario
from app.api.routes import relatorios, matriz_planejamento, dashboard, filtros


v1_router = APIRouter()

v1_router.include_router(calendario.router, prefix="/calendario", tags=["Calendário"])
v1_router.include_router(relatorios.router, prefix="/relatorios", tags=["Relatórios"])
v1_router.include_router(matriz_planejamento.router, prefix="/matriz-planejamento", tags=["Matriz de Planejamento"])
v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
v1_router.include_router(filtros.router, prefix="/filtros", tags=["Filtros"])
