import logging
logging.basicConfig(level=logging.INFO)
logging.info("[SINCRONIZACOES_JIRA] Arquivo sincronizacoes_jira.py foi carregado!")
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Path
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.security import get_current_admin_user
from app.db.session import get_db, get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.usuario import UsuarioInDB
from app.services.sincronizacao_jira_service import SincronizacaoJiraService
from app.services.log_service import LogService
from app.integrations.jira_client import JiraClient

router = APIRouter(tags=["Integração Jira"])

class SincronizacaoJiraOut(BaseModel):
    id: int
    data_inicio: str
    data_fim: str
    status: str
    mensagem: Optional[str] = None
    quantidade_apontamentos_processados: Optional[int] = None

from fastapi.responses import JSONResponse

@router.get("/", response_model=Dict[str, Any])
async def listar_sincronizacoes(
    skip: int = Query(0, description="Número de registros a pular para paginação"),
    limit: int = Query(50, description="Número máximo de registros a retornar"),
    status: Optional[str] = Query(None, description="Filtrar por status (RECEBIDO, SUCESSO, ERRO)"),
    tipo_evento: Optional[str] = Query(None, description="Filtrar por tipo de evento (worklog_created, worklog_updated, worklog_deleted)"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Lista o histórico de sincronizações com o Jira (paginado).
    
    - **skip**: Quantidade de registros a pular
    - **limit**: Quantidade máxima de registros
    - **status**: Filtrar por status específico
    - **tipo_evento**: Filtrar por tipo de evento específico
    
    Retorna um objeto com items, total, skip e limit.
    """
    sincronizacao_service = SincronizacaoJiraService(db)
    result = await sincronizacao_service.listar_sincronizacoes(
        skip=skip,
        limit=limit,
        status=status,
        tipo_evento=tipo_evento
    )
    return JSONResponse(content=result)


@router.get("/{id}", response_model=SincronizacaoJiraOut)
async def obter_sincronizacao(
    id: int = Path(..., description="ID da sincronização"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Obtém detalhes de uma sincronização específica.
    
    - **id**: ID da sincronização
    
    Retorna os detalhes da sincronização.
    """
    sincronizacao_service = SincronizacaoJiraService(db)
    sincronizacao = await sincronizacao_service.obter_sincronizacao(id)
    
    if not sincronizacao:
        raise HTTPException(status_code=404, detail="Sincronização não encontrada")
        
    return sincronizacao


def executar_sincronizacao_background(db: Session, dias: int, usuario_id: int):
    """
    Executa a sincronização em segundo plano.
    
    Args:
        db: Sessão do banco de dados
        dias: Número de dias para sincronizar
        usuario_id: ID do usuário que solicitou a sincronização
    """
    # Criar nova sessão para a tarefa em background
    with db.session.registry().main_engine.connect() as conn:
        with Session(bind=conn) as session:
            try:
                sincronizacao_service = SincronizacaoJiraService(session)
                jira_client = JiraClient()
                log_service = LogService(session)
                
                # Registrar início da sincronização
                log_service.registrar_acao(
                    acao="INICIAR_SINCRONIZACAO",
                    entidade="sincronizacao_jira",
                    usuario_id=usuario_id,
                    detalhes=f"Sincronização manual iniciada para os últimos {dias} dias"
                )
                
                # Determinar data de início da sincronização
                since = datetime.now() - timedelta(days=dias)
                
                # Executar sincronização
                result = jira_client.sync_worklogs_since(since)
                
                # Registrar resultados
                log_service.registrar_acao(
                    acao="CONCLUIR_SINCRONIZACAO",
                    entidade="sincronizacao_jira",
                    usuario_id=usuario_id,
                    detalhes=f"Sincronização concluída: {result['processed']} de {result['total']} worklogs processados, {result['errors']} erros"
                )
                
            except Exception as e:
                # Registrar erro
                log_service.registrar_acao(
                    acao="ERRO_SINCRONIZACAO",
                    entidade="sincronizacao_jira",
                    usuario_id=usuario_id,
                    detalhes=f"Erro na sincronização manual: {str(e)}"
                )


@router.post("/manual")
def iniciar_sincronizacao_manual(
    background_tasks: BackgroundTasks,
    dias: int = Query(7, description="Número de dias para sincronizar"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Inicia uma sincronização manual com o Jira.
    
    - **dias**: Número de dias para olhar para trás
    
    Retorna status da solicitação.
    """
    log_service = LogService(db)
    
    # Registrar solicitação
    log_service.registrar_acao(
        acao="SOLICITAR_SINCRONIZACAO",
        entidade="sincronizacao_jira",
        usuario=current_user,
        detalhes=f"Solicitação de sincronização manual para os últimos {dias} dias"
    )
    
    # Iniciar sincronização em segundo plano
    background_tasks.add_task(
        executar_sincronizacao_background,
        db=db,
        dias=dias,
        usuario_id=current_user.id
    )
    
    return {
        "status": "iniciada",
        "mensagem": f"Sincronização manual iniciada para os últimos {dias} dias. Verifique os logs para acompanhar o progresso."
    }

# NOVO ENDPOINT COMPATÍVEL COM O FRONTEND

import logging

@router.post(
    "/importar-tudo",
    summary="Sincronização completa do Jira",
    description="Inicia a sincronização completa do Jira (todos os projetos, issues e worklogs). Protegido: requer autenticação de admin. Retorna status de processamento.",
    response_model=dict,
    responses={
        200: {
            "description": "Sincronização completa do Jira iniciada com sucesso.",
            "content": {
                "application/json": {
                    "example": {"status": "processing", "message": "Sincronização completa do Jira iniciada."}
                }
            }
        },
        500: {"description": "Erro ao agendar sincronização total do Jira."}
    }
)
async def importar_tudo_jira(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Inicia a sincronização completa do Jira (todos os projetos, issues e worklogs).
    - **Protegido**: requer autenticação de admin.
    - **Retorno**: status de processamento da sincronização.
    """
    logger = logging.getLogger("sincronizacoes_jira.importar_tudo")
    logger.info("[INICIO] Chamada ao endpoint /importar-tudo por usuário %s (id=%s)", current_user.username, current_user.id)
    try:
        async def sync_bg(db: AsyncSession):
            logger.info("[BG] Iniciando sincronização total em background")
            try:
                service = SincronizacaoJiraService(db)
                # Não passar o ID do usuário para evitar erro de chave estrangeira
                await service.sincronizar_tudo(usuario_id=None)
                logger.info("[BG] Sincronização total concluída")
            except Exception as e:
                logger.error("[BG] Erro na sincronização total: %s", str(e))
        background_tasks.add_task(sync_bg, db)
        logger.info("[FIM] Sincronização total agendada para usuario_id=%s", current_user.id)
        return {"status": "processing", "message": "Sincronização completa do Jira iniciada."}
    except Exception as exc:
        logger.error("[ERRO] Falha ao agendar sincronização total: %s", str(exc))
        raise HTTPException(status_code=500, detail=f"Erro ao agendar sincronização total: {str(exc)}")
        raise HTTPException(status_code=500, detail="Erro ao agendar sincronização total do Jira.")

@router.post("/importar")
async def importar_sincronizacao_jira(
    background_tasks: BackgroundTasks,
    dias: int = Query(7, description="Número de dias para sincronizar"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Endpoint compatível com o frontend para iniciar sincronização manual do Jira.
    """
    log_service = LogService(db)
    log_service.registrar_acao(
        acao="SOLICITAR_SINCRONIZACAO",
        entidade="sincronizacao_jira",
        usuario=current_user,
        detalhes=f"Solicitação de sincronização manual via /importar para os últimos {dias} dias"
    )
    background_tasks.add_task(
        executar_sincronizacao_background,
        db=db,
        dias=dias,
        usuario_id=current_user.id
    )
    return {
        "status": "iniciada",
        "mensagem": f"Sincronização manual (via /importar) iniciada para os últimos {dias} dias. Verifique os logs para acompanhar o progresso."
    }