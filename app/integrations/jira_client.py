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
        logger.info(f"[JIRA_CLIENT] Inicializado com base_url={self.base_url}, username={self.username}")

    def fetch_all_projects_issues_worklogs(self) -> dict:
        """
        Busca todos os projetos, issues e worklogs do Jira, com paginação.
        Retorna um resumo da sincronização.
        """
        logger.info(f"[JIRA_FETCH] Iniciando busca de todos os projetos, issues e worklogs")
        
        # 1. Buscar todos os projetos com paginação
        all_projects = []
        start_at = 0
        max_results = 50
        
        logger.info(f"[JIRA_FETCH] Buscando projetos com paginação (max_results={max_results})")
        try:
            while True:
                # Usar o mesmo endpoint que foi usado no Postman
                endpoint = f"/rest/api/3/project/search?startAt={start_at}&maxResults={max_results}"
                logger.info(f"[JIRA_ENDPOINT] Endpoint completo: {self.base_url}{endpoint}")
                logger.info(f"[JIRA_FETCH] Chamando endpoint: {endpoint}")
                resp = self._make_request("GET", endpoint)
                values = resp.get("values", [])
                logger.info(f"[JIRA_FETCH] Recebidos {len(values)} projetos")
                all_projects.extend(values)
                if resp.get("isLast", False) or len(values) < max_results:
                    break
                start_at += max_results
            logger.info(f"[JIRA_FETCH] Total de projetos encontrados: {len(all_projects)}")
        except Exception as e:
            logger.error(f"[JIRA_FETCH] Erro ao buscar projetos: {str(e)}")
            raise
        # 2. Para cada projeto, buscar todos os issues (paginação)
        all_issues = []
        for proj in all_projects:
            project_key = proj.get("key")
            if not project_key:
                continue
            issues_start = 0
            while True:
                jql = f"project={project_key}"
                endpoint = f"/rest/api/3/search?jql={jql}&fields=worklog&startAt={issues_start}&maxResults={max_results}"
                issues_resp = self._make_request("GET", endpoint)
                issues = issues_resp.get("issues", [])
                all_issues.extend(issues)
                if len(issues) < max_results:
                    break
                issues_start += max_results
        # 3. Para cada issue, buscar todos os worklogs (paginação)
        all_worklogs = []
        for issue in all_issues:
            issue_key = issue.get("key")
            if not issue_key:
                continue
            worklog_start = 0
            while True:
                endpoint = f"/rest/api/3/issue/{issue_key}/worklog?startAt={worklog_start}&maxResults={max_results}"
                worklog_resp = self._make_request("GET", endpoint)
                worklogs = worklog_resp.get("worklogs", [])
                all_worklogs.extend(worklogs)
                if len(worklogs) < max_results:
                    break
                worklog_start += max_results
        return {
            "total_projects": len(all_projects),
            "total_issues": len(all_issues),
            "total_worklogs": len(all_worklogs),
            "projects": all_projects,
            "issues": all_issues,
            "worklogs": all_worklogs
        }

    
    
    def get_issues(self, jql: str, fields: str = "summary") -> dict:
        endpoint = f"/search?jql={jql}&fields={fields}"
        return self._make_request("GET", endpoint)

    def get_worklogs(self, issue_id_or_key: str) -> dict:
        endpoint = f"/issue/{issue_id_or_key}/worklog"
        return self._make_request("GET", endpoint)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Realiza uma requisição para a API do Jira.

        Args:
            method (str): Método HTTP (GET, POST, PUT, DELETE)
            endpoint (str): Endpoint da API (ex: /rest/api/3/issue)
            data (Optional[Dict[str, Any]], optional): Dados para enviar no corpo da requisição. Defaults to None.

        Returns:
            Dict[str, Any]: Resposta da API em formato JSON

        Raises:
            Exception: Erro na requisição
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        auth = (self.username, self.api_token)

        logger.info(f"[JIRA_REQUEST] {method} {url}")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, auth=auth)
            elif method == "POST":
                response = requests.post(url, headers=headers, auth=auth, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, auth=auth, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, auth=auth)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")

            logger.info(f"[JIRA_RESPONSE] Status: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error(f"[JIRA_ERROR] {response.status_code}: {response.text}")
            
            response.raise_for_status()  # Lança exceção para códigos de erro HTTP
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"[JIRA_ERROR] Erro na requisição para {url}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"[JIRA_ERROR] Status: {e.response.status_code}, Resposta: {e.response.text}")
            raise Exception(f"Erro na requisição para {url}: {str(e)}")
        except Exception as e:
            logger.error(f"[JIRA_ERROR] Erro inesperado: {str(e)}")
            raise
            
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