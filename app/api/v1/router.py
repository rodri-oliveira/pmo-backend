from fastapi import APIRouter
from app.api.v1.endpoints import calendario

v1_router = APIRouter()

v1_router.include_router(calendario.router, prefix="/calendario", tags=["Calendário"])
