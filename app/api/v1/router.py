from fastapi import APIRouter
from app.api.v1.endpoints import calendario
from app.api.routes import relatorios


v1_router = APIRouter()

v1_router.include_router(calendario.router, prefix="/calendario", tags=["Calendário"])
v1_router.include_router(relatorios.router, prefix="/relatorios", tags=["Relatórios"])
