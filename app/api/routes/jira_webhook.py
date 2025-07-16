import logging
from fastapi import APIRouter, Depends, HTTPException, Body, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.jira_webhook_service import JiraWebhookService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Jira Webhooks"])


@router.post("/jira/webhooks/worklog", status_code=status.HTTP_200_OK)
async def process_jira_worklog_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint para receber webhooks do Jira relacionados a worklog.
    Não requer autenticação pois é chamado pelo Jira.
    
    Args:
        request: Objeto de requisição para obter o payload JSON
        db: Sessão do banco de dados
    
    Returns:
        dict: Confirmação de processamento
    
    Raises:
        HTTPException: Se houver erro no processamento
    """
    try:
        # Pega o payload completo do request
        payload = await request.json()
        
        service = JiraWebhookService(db)
        result = service.process_worklog_webhook(payload)
        
        return {"status": "success", "message": "Webhook processado", "details": result}
    except Exception as e:
        # Não lançamos 500 para o Jira para evitar retentativas, mas logamos o erro
        # Seria ideal ter um sistema de logging adequado
        logger.error(f"Erro ao processar webhook Jira: {str(e)}")
        return {
            "status": "error", 
            "message": "Erro ao processar webhook", 
            "details": str(e)
        } 