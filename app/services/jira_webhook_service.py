from typing import Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.apontamento_repository import ApontamentoRepository
from app.repositories.recurso_repository import RecursoRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.sincronizacao_jira_repository import SincronizacaoJiraRepository
from app.db.orm_models import FonteApontamento

class JiraWebhookService:
    def __init__(self, db: Session):
        self.db = db
        self.apontamento_repository = ApontamentoRepository(db)
        self.recurso_repository = RecursoRepository(db)
        self.projeto_repository = ProjetoRepository(db)
        self.sincronizacao_repository = SincronizacaoJiraRepository(db)
    
    def process_worklog_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa webhook do Jira relacionado a worklog.
        
        Args:
            payload: Payload do webhook
            
        Returns:
            Dict[str, Any]: Resultado do processamento
            
        Raises:
            ValueError: Se houver erro no processamento
        """
        # Registrar início da sincronização
        sync_data = {
            "data_inicio": datetime.utcnow(),
            "status": "PROCESSING",
            "mensagem": f"Processando webhook: {payload.get('webhookEvent', 'unknown')}",
            "quantidade_apontamentos_processados": 0
        }
        sync_record = self.sincronizacao_repository.create(sync_data)
        
        try:
            # Extrair tipo de evento
            webhook_event = payload.get("webhookEvent", "")
            
            # Verificar se é um evento de worklog
            if "worklog" not in webhook_event:
                self._update_sync_record(sync_record.id, "IGNORED", f"Não é um evento de worklog: {webhook_event}", 0)
                return {"status": "ignored", "reason": f"Não é um evento de worklog: {webhook_event}"}
            
            # Processa baseado no tipo de evento
            result = None
            if webhook_event == "worklog_created":
                result = self._process_worklog_created(payload)
            elif webhook_event == "worklog_updated":
                result = self._process_worklog_updated(payload)
            elif webhook_event == "worklog_deleted":
                result = self._process_worklog_deleted(payload)
            else:
                self._update_sync_record(sync_record.id, "IGNORED", f"Tipo de evento de worklog não suportado: {webhook_event}", 0)
                return {"status": "ignored", "reason": f"Tipo de evento de worklog não suportado: {webhook_event}"}
            
            # Atualizar registro de sincronização como sucesso
            self._update_sync_record(sync_record.id, "SUCCESS", f"Webhook processado com sucesso: {result['action']}", 1)
            return result
            
        except Exception as e:
            # Atualizar registro de sincronização como erro
            self._update_sync_record(sync_record.id, "ERROR", f"Erro: {str(e)}", 0)
            raise
    
    def _process_worklog_created(self, payload: Dict) -> Dict:
        """Processa evento de criação de worklog"""
        # Extrair dados do worklog
        worklog_data = self._extract_worklog_data(payload)
        
        # Criar apontamento a partir dos dados do worklog
        self.apontamento_repository.sync_jira_apontamento(worklog_data)
        
        return {
            "status": "success", 
            "action": "created", 
            "worklog_id": worklog_data["jira_worklog_id"]
        }
    
    def _process_worklog_updated(self, payload: Dict) -> Dict:
        """Processa evento de atualização de worklog"""
        # Extrair dados do worklog
        worklog_data = self._extract_worklog_data(payload)
        
        # Atualizar apontamento existente
        self.apontamento_repository.sync_jira_apontamento(worklog_data)
        
        return {
            "status": "success", 
            "action": "updated", 
            "worklog_id": worklog_data["jira_worklog_id"]
        }
    
    def _process_worklog_deleted(self, payload: Dict) -> Dict:
        """Processa evento de exclusão de worklog"""
        # Extrair ID do worklog
        worklog_id = self._extract_worklog_id_from_delete_event(payload)
        
        # Excluir apontamento correspondente
        self.apontamento_repository.delete_from_jira(worklog_id)
        
        return {
            "status": "success", 
            "action": "deleted", 
            "worklog_id": worklog_id
        }
    
    def _extract_worklog_data(self, payload: Dict) -> Dict:
        """
        Extrai dados relevantes do payload do webhook.
        
        Args:
            payload: Payload do webhook
            
        Returns:
            Dict: Dados formatados para o apontamento
            
        Raises:
            ValueError: Se dados obrigatórios estiverem ausentes ou não puderem ser mapeados
        """
        # Implementação simplificada - em produção, seria mais robusta
        # Extrair dados do worklog
        worklog = payload.get("worklog", {})
        issue = payload.get("issue", {})
        
        # IDs importantes
        jira_worklog_id = worklog.get("id")
        if not jira_worklog_id:
            raise ValueError("ID do worklog não encontrado no payload")
        
        jira_issue_key = issue.get("key")
        if not jira_issue_key:
            raise ValueError("Chave da issue não encontrada no payload")
        
        # Dados do autor
        author_account_id = worklog.get("author", {}).get("accountId")
        if not author_account_id:
            raise ValueError("ID da conta do autor não encontrado no payload")
        
        # Buscar recurso pelo jira_user_id
        recurso = self.recurso_repository.get_by_jira_user_id(author_account_id)
        if not recurso:
            raise ValueError(f"Recurso com jira_user_id={author_account_id} não encontrado")
        
        # Buscar projeto pelo jira_project_key
        jira_project_key = issue.get("fields", {}).get("project", {}).get("key")
        if not jira_project_key:
            raise ValueError("Chave do projeto não encontrada no payload")
        
        projeto = self.projeto_repository.get_by_jira_project_key(jira_project_key)
        if not projeto:
            raise ValueError(f"Projeto com jira_project_key={jira_project_key} não encontrado")
        
        # Dados do worklog
        started = worklog.get("started")  # Formato ISO: 2023-05-02T09:00:00.000+0000
        time_spent_seconds = worklog.get("timeSpentSeconds", 0)
        hours_spent = time_spent_seconds / 3600  # Converter de segundos para horas
        comment = worklog.get("comment", "")
        
        # Montar dados para o apontamento
        return {
            "jira_worklog_id": jira_worklog_id,
            "recurso_id": recurso.id,
            "projeto_id": projeto.id,
            "jira_issue_key": jira_issue_key,
            "data_hora_inicio_trabalho": started,
            "data_apontamento": started.split("T")[0] if started else None,  # Extrair apenas a data
            "horas_apontadas": hours_spent,
            "descricao": comment,
            "fonte_apontamento": "JIRA",
            "data_sincronizacao_jira": "now()"  # Função SQL para data/hora atual
        }
    
    def _extract_worklog_id_from_delete_event(self, payload: Dict) -> str:
        """Extrai o ID do worklog em um evento de exclusão"""
        worklog = payload.get("worklog", {})
        jira_worklog_id = worklog.get("id")
        if not jira_worklog_id:
            raise ValueError("ID do worklog não encontrado no payload de exclusão")
        return jira_worklog_id
    
    def _register_sync_error(self, webhook_event: str, error_message: str) -> None:
        """Registra erro de sincronização na tabela sincronizacao_jira"""
        self.sincronizacao_repository.create({
            "data_inicio": "now()",
            "data_fim": "now()",
            "status": "ERROR",
            "mensagem": f"Erro ao processar webhook {webhook_event}: {error_message}",
            "quantidade_apontamentos_processados": 0
        }) 