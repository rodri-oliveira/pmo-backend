from typing import Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.apontamento_repository import ApontamentoRepository
from app.repositories.recurso_repository import RecursoRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.sincronizacao_jira_repository import SincronizacaoJiraRepository
from app.db.orm_models import FonteApontamento
from fastapi import HTTPException, status
import json
import logging

logger = logging.getLogger(__name__)

class JiraWebhookService:
    def __init__(self, db: Session):
        self.db = db
        self.apontamento_repository = ApontamentoRepository(db)
        self.recurso_repository = RecursoRepository(db)
        self.projeto_repository = ProjetoRepository(db)
        self.sincronizacao_repository = SincronizacaoJiraRepository(db)
    
    def process_worklog_webhook(self, payload: Dict[str, Any], webhook_event: str) -> Dict[str, Any]:
        """
        Processa um webhook do Jira relacionado a worklog.
        
        Args:
            payload: Dados do webhook
            webhook_event: Tipo de evento (worklog_created, worklog_updated, worklog_deleted)
            
        Returns:
            Resultado do processamento
        """
        # Registrar recebimento do webhook
        self._log_webhook_received(webhook_event, payload)
        
        try:
            # Extrair informações relevantes do payload
            worklog_data = self._extract_worklog_data(payload)
            
            # Mapear usuário do Jira para recurso interno
            recurso = self._map_jira_user_to_recurso(worklog_data["account_id"])
            if not recurso:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Recurso não encontrado para o usuário Jira com account_id: {worklog_data['account_id']}"
                )
            
            # Mapear issue do Jira para projeto interno
            projeto = self._map_jira_issue_to_projeto(worklog_data["project_key"], worklog_data["issue_id"])
            if not projeto:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Projeto não encontrado para a issue Jira: {worklog_data['issue_key']}"
                )
            
            # Processar o evento específico
            if webhook_event == "worklog_created" or webhook_event == "worklog_updated":
                apontamento_data = {
                    "recurso_id": recurso.id,
                    "projeto_id": projeto.id,
                    "data_apontamento": worklog_data["data_apontamento"],
                    "horas_apontadas": worklog_data["horas_apontadas"],
                    "descricao": worklog_data["comentario"],
                    "jira_issue_key": worklog_data["issue_key"],
                    "jira_issue_id": worklog_data["issue_id"]
                }
                
                apontamento = self.apontamento_repository.sync_jira_apontamento(
                    worklog_data["worklog_id"],
                    apontamento_data
                )
                
                # Registrar sincronização bem-sucedida
                self._log_sync_success(webhook_event, apontamento.id, worklog_data["worklog_id"])
                
                return {
                    "status": "success",
                    "message": f"Apontamento {webhook_event} processado com sucesso",
                    "apontamento_id": apontamento.id
                }
                
            elif webhook_event == "worklog_deleted":
                success = self.apontamento_repository.delete_from_jira(worklog_data["worklog_id"])
                
                if success:
                    # Registrar deleção bem-sucedida
                    self._log_sync_success(webhook_event, None, worklog_data["worklog_id"])
                    
                    return {
                        "status": "success",
                        "message": "Apontamento removido com sucesso"
                    }
                else:
                    return {
                        "status": "warning",
                        "message": "Apontamento não encontrado para remoção"
                    }
            
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Evento de webhook não suportado: {webhook_event}"
                )
                
        except Exception as e:
            # Registrar erro
            self._log_sync_error(webhook_event, str(e), payload)
            
            # Re-lançar exceção para tratamento adequado na API
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao processar webhook: {str(e)}"
            )
    
    def _extract_worklog_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai dados relevantes do worklog do payload do webhook.
        
        Args:
            payload: Dados do webhook
            
        Returns:
            Dados extraídos do worklog
        """
        # Implementação depende da estrutura exata do payload do Jira
        # Este é um exemplo simplificado
        try:
            worklog = payload.get("worklog", {})
            issue = payload.get("issue", {})
            
            return {
                "worklog_id": worklog.get("id"),
                "account_id": worklog.get("author", {}).get("accountId"),
                "horas_apontadas": worklog.get("timeSpentSeconds", 0) / 3600,  # Converter segundos para horas
                "data_apontamento": worklog.get("started"),  # Formato ISO
                "comentario": worklog.get("comment", ""),
                "issue_id": issue.get("id"),
                "issue_key": issue.get("key"),
                "project_key": issue.get("fields", {}).get("project", {}).get("key")
            }
        except Exception as e:
            logger.error(f"Erro ao extrair dados do worklog: {str(e)}")
            logger.debug(f"Payload: {json.dumps(payload)}")
            raise ValueError(f"Erro ao extrair dados do worklog: {str(e)}")
    
    def _map_jira_user_to_recurso(self, account_id: str) -> Optional[Any]:
        """
        Mapeia um usuário do Jira para um recurso interno.
        
        Args:
            account_id: ID da conta do usuário no Jira
            
        Returns:
            Recurso correspondente ou None
        """
        return self.recurso_repository.get_by_jira_account_id(account_id)
    
    def _map_jira_issue_to_projeto(self, project_key: str, issue_id: str) -> Optional[Any]:
        """
        Mapeia uma issue do Jira para um projeto interno.
        
        Args:
            project_key: Chave do projeto no Jira
            issue_id: ID da issue no Jira
            
        Returns:
            Projeto correspondente ou None
        """
        # Primeiro tenta encontrar por mapeamento direto de issue
        projeto = self.projeto_repository.get_by_jira_issue_id(issue_id)
        if projeto:
            return projeto
            
        # Se não encontrar, busca pelo projeto relacionado
        return self.projeto_repository.get_by_jira_project_key(project_key)
    
    def _log_webhook_received(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Registra o recebimento de um webhook.
        
        Args:
            event_type: Tipo de evento
            payload: Dados do webhook
        """
        logger.info(f"Webhook {event_type} recebido")
        logger.debug(f"Payload: {json.dumps(payload)}")
        
        # Registrar na tabela de sincronização
        self.sincronizacao_repository.create({
            "tipo_evento": event_type,
            "payload": json.dumps(payload),
            "status": "RECEBIDO",
            "data_hora": "NOW()"  # Será convertido para a função NOW() do banco
        })
    
    def _log_sync_success(self, event_type: str, apontamento_id: Optional[int], worklog_id: str) -> None:
        """
        Registra o sucesso de uma sincronização.
        
        Args:
            event_type: Tipo de evento
            apontamento_id: ID do apontamento sincronizado
            worklog_id: ID do worklog no Jira
        """
        logger.info(f"Sincronização {event_type} bem-sucedida")
        logger.debug(f"Apontamento ID: {apontamento_id}, Worklog ID: {worklog_id}")
        
        # Registrar na tabela de sincronização
        self.sincronizacao_repository.create({
            "data_inicio": "now()",
            "data_fim": "now()",
            "status": "SUCCESS",
            "mensagem": f"Webhook {event_type} processado com sucesso",
            "quantidade_apontamentos_processados": 1
        })
    
    def _log_sync_error(self, event_type: str, error_message: str, payload: Dict[str, Any]) -> None:
        """
        Registra um erro de sincronização.
        
        Args:
            event_type: Tipo de evento
            error_message: Mensagem de erro
            payload: Dados do webhook
        """
        logger.error(f"Erro ao processar webhook {event_type}: {error_message}")
        logger.debug(f"Payload: {json.dumps(payload)}")
        
        # Registrar na tabela de sincronização
        self.sincronizacao_repository.create({
            "data_inicio": "now()",
            "data_fim": "now()",
            "status": "ERROR",
            "mensagem": f"Erro ao processar webhook {event_type}: {error_message}",
            "quantidade_apontamentos_processados": 0
        }) 