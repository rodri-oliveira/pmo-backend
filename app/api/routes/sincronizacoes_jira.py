from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Path
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.security import get_current_admin_user
from app.db.session import get_db
from app.models.usuario import UsuarioInDB
from app.services.sincronizacao_jira_service import SincronizacaoJiraService
from app.services.log_service import LogService
from app.integrations.jira_client import JiraClient

router = APIRouter(prefix="/sincronizacoes-jira", tags=["Integração Jira"])


@router.get("/")
def listar_sincronizacoes(
    dias: Optional[int] = Query(7, description="Número de dias para listar sincronizações"),
    status: Optional[str] = Query(None, description="Filtrar por status (RECEBIDO, SUCESSO, ERRO)"),
    tipo_evento: Optional[str] = Query(None, description="Filtrar por tipo de evento (worklog_created, worklog_updated, worklog_deleted)"),
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Lista o histórico de sincronizações com o Jira.
    
    - **dias**: Número de dias para olhar para trás
    - **status**: Filtrar por status específico
    - **tipo_evento**: Filtrar por tipo de evento específico
    
    Retorna uma lista de sincronizações.
    """
    sincronizacao_service = SincronizacaoJiraService(db)
    
    return sincronizacao_service.listar_sincronizacoes(
        dias=dias,
        status=status,
        tipo_evento=tipo_evento
    )


@router.get("/{id}")
def obter_sincronizacao(
    id: int = Path(..., description="ID da sincronização"),
    db: Session = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Obtém detalhes de uma sincronização específica.
    
    - **id**: ID da sincronização
    
    Retorna os detalhes da sincronização.
    """
    sincronizacao_service = SincronizacaoJiraService(db)
    sincronizacao = sincronizacao_service.obter_sincronizacao(id)
    
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
    db: Session = Depends(get_db),
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