from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.security import get_current_admin_user
from app.db.session import get_db
from app.models.usuario import UsuarioInDB
from app.services.log_service import LogService

router = APIRouter(prefix="/logs-atividade", tags=["Administração"])

@router.get("/")
def listar_logs(
    entidade: Optional[str] = Query(None, description="Filtrar por entidade"),
    entidade_id: Optional[int] = Query(None, description="Filtrar por ID da entidade"),
    usuario_id: Optional[int] = Query(None, description="Filtrar por ID do usuário"),
    acao: Optional[str] = Query(None, description="Filtrar por tipo de ação"),
    data_inicio: Optional[datetime] = Query(None, description="Data inicial"),
    data_fim: Optional[datetime] = Query(None, description="Data final"),
    limite: int = Query(100, description="Número máximo de logs a retornar"),
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Lista logs de atividade do sistema.
    
    - **entidade**: Filtrar por entidade específica
    - **entidade_id**: Filtrar por ID de entidade específica
    - **usuario_id**: Filtrar por usuário específico
    - **acao**: Filtrar por tipo de ação
    - **data_inicio**: Filtrar a partir desta data
    - **data_fim**: Filtrar até esta data
    - **limite**: Número máximo de logs a retornar
    
    Retorna uma lista de logs filtrados.
    """
    log_service = LogService(db)
    
    return log_service.buscar_logs(
        entidade=entidade,
        entidade_id=entidade_id,
        usuario_id=usuario_id,
        acao=acao,
        data_inicio=data_inicio,
        data_fim=data_fim,
        limite=limite
    )

@router.get("/entidades")
def listar_entidades_com_logs(
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Lista as entidades que possuem logs registrados.
    
    Retorna uma lista de nomes de entidades.
    """
    # Implementação simplificada - em um cenário real seria melhor
    # ter uma query específica no repositório para isso
    log_service = LogService(db)
    logs = log_service.buscar_logs(limite=1000)  # Buscar um número razoável de logs
    
    # Extrair entidades únicas
    entidades = set(log["entidade"] for log in logs)
    
    return {"entidades": list(entidades)}

@router.get("/acoes")
def listar_tipos_acoes(
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Lista os tipos de ações registradas nos logs.
    
    Retorna uma lista de tipos de ações.
    """
    # Implementação simplificada - em um cenário real seria melhor
    # ter uma query específica no repositório para isso
    log_service = LogService(db)
    logs = log_service.buscar_logs(limite=1000)  # Buscar um número razoável de logs
    
    # Extrair tipos de ações únicos
    acoes = set(log["acao"] for log in logs)
    
    return {"acoes": list(acoes)} 