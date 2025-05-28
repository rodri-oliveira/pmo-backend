import requests
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

class JiraClient:
    """
    Cliente para integração com a API do Jira.
    """
    
    def __init__(self):
        """
        Inicializa o cliente Jira com as configurações padrão.
        """
        self.base_url = settings.JIRA_BASE_URL.rstrip('/')
        self.api_url = f"{self.base_url}/rest/api/3"
        self.username = settings.JIRA_USERNAME
        self.api_token = settings.JIRA_API_TOKEN
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get_issues(self, jql: str, fields: str = "summary") -> dict:
        endpoint = f"/search?jql={jql}&fields={fields}"
        return self._make_request("GET", endpoint)

    def get_worklogs(self, issue_id_or_key: str) -> dict:
        endpoint = f"/issue/{issue_id_or_key}/worklog"
        return self._make_request("GET", endpoint)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Realiza uma requisição HTTP para a API do Jira.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API
            data: Dados para enviar (para POST/PUT)
            
        Returns:
            Resposta da API
            
        Raises:
            Exception: Se a requisição falhar
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=(self.username, self.api_token),
                headers=self.headers,
                json=data
            )
            
            response.raise_for_status()
            
            if response.status_code == 204:  # No Content
                return {}
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição Jira: {str(e)}")
            
            # Tentar extrair detalhes do erro
            error_details = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_details = json.dumps(error_data)
                except:
                    error_details = e.response.text
            
            raise Exception(f"Erro na integração com Jira: {error_details}")
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Obtém detalhes de uma issue.
        
        Args:
            issue_key: Chave da issue (ex: PROJ-123)
            
        Returns:
            Dados da issue
        """
        endpoint = f"/rest/api/3/issue/{issue_key}"
        return self._make_request("GET", endpoint)
    
    def get_worklogs(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Obtém todos os worklogs de uma issue.
        
        Args:
            issue_key: Chave da issue (ex: PROJ-123)
            
        Returns:
            Lista de worklogs
        """
        endpoint = f"/rest/api/3/issue/{issue_key}/worklog"
        response = self._make_request("GET", endpoint)
        return response.get("worklogs", [])
    
    def get_project(self, project_key: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um projeto.
        
        Args:
            project_key: Chave do projeto (ex: PROJ)
            
        Returns:
            Dados do projeto
        """
        endpoint = f"/rest/api/3/project/{project_key}"
        return self._make_request("GET", endpoint)
    
    def search_issues(self, jql: str, fields: List[str] = None, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Busca issues usando JQL.
        
        Args:
            jql: Consulta JQL
            fields: Campos a retornar
            max_results: Máximo de resultados
            
        Returns:
            Lista de issues
        """
        endpoint = "/rest/api/3/search"
        
        if fields is None:
            fields = ["summary", "status", "assignee", "project"]
            
        data = {
            "jql": jql,
            "fields": fields,
            "maxResults": max_results
        }
        
        response = self._make_request("POST", endpoint, data)
        return response.get("issues", [])
    
    def get_updated_worklogs(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Obtém worklogs atualizados desde uma data específica.
        
        Args:
            since: Data a partir da qual buscar atualizações
            
        Returns:
            Dados de worklogs atualizados
        """
        endpoint = "/rest/api/3/worklog/updated"
        
        params = {}
        if since:
            # Converter para timestamp em milissegundos
            since_ms = int(since.timestamp() * 1000)
            params = {"since": since_ms}
            endpoint = f"{endpoint}?since={since_ms}"
            
        return self._make_request("GET", endpoint)
    
    def get_worklog_by_id(self, worklog_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um worklog específico.
        
        Args:
            worklog_id: ID do worklog
            
        Returns:
            Dados do worklog
        """
        endpoint = f"/rest/api/3/worklog/{worklog_id}"
        return self._make_request("GET", endpoint)
    
    def get_user(self, account_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um usuário.
        
        Args:
            account_id: ID da conta do usuário
            
        Returns:
            Dados do usuário
        """
        endpoint = f"/rest/api/3/user?accountId={account_id}"
        return self._make_request("GET", endpoint)
    
    def get_recent_worklogs(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Obtém worklogs registrados nos últimos dias.
        
        Args:
            days: Número de dias para olhar para trás
            
        Returns:
            Lista de worklogs recentes
        """
        since = datetime.now() - timedelta(days=days)
        
        # Obter IDs de worklogs atualizados
        updated = self.get_updated_worklogs(since)
        
        # Buscar cada worklog individualmente
        worklogs = []
        for value in updated.get("values", []):
            worklog_id = value.get("worklogId")
            try:
                worklog = self.get_worklog_by_id(worklog_id)
                worklogs.append(worklog)
            except Exception as e:
                logger.warning(f"Erro ao obter worklog {worklog_id}: {str(e)}")
                
        return worklogs
    
    def sync_worklogs_since(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Sincroniza worklogs desde uma data específica.
        
        Args:
            since: Data a partir da qual sincronizar
            
        Returns:
            Resumo da sincronização
        """
        if since is None:
            # Se não houver data, olha para os últimos 7 dias
            since = datetime.now() - timedelta(days=7)
            
        try:
            # Obter worklogs atualizados
            updated = self.get_updated_worklogs(since)
            
            # Estatísticas
            total = len(updated.get("values", []))
            processed = 0
            errors = 0
            
            # Processar cada worklog
            for value in updated.get("values", []):
                worklog_id = value.get("worklogId")
                try:
                    # Obter detalhes do worklog
                    worklog = self.get_worklog_by_id(worklog_id)
                    
                    # TODO: Aqui entraria a lógica para salvar no banco de dados
                    # Isso seria feito pelo serviço que usa este cliente
                    
                    processed += 1
                except Exception as e:
                    logger.error(f"Erro ao processar worklog {worklog_id}: {str(e)}")
                    errors += 1
            
            return {
                "total": total,
                "processed": processed,
                "errors": errors,
                "since": since.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro na sincronização de worklogs: {str(e)}")
            raise 