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
        
        # Verificar credenciais
        logger.info(f"[JIRA_CREDENTIALS] Base URL: {self.base_url}")
        logger.info(f"[JIRA_CREDENTIALS] Username: {self.username}")
        # Não logar o token completo por segurança
        if self.api_token:
            token_preview = self.api_token[:5] + "..." + self.api_token[-5:] if len(self.api_token) > 10 else "***"
            logger.info(f"[JIRA_CREDENTIALS] API Token: {token_preview}")
        else:
            logger.error(f"[JIRA_CREDENTIALS] API Token não definido!")
        
        # Testar conexão com o Jira antes de buscar projetos
        try:
            # Endpoint simples para testar conexão
            test_endpoint = "/rest/api/3/myself"
            logger.info(f"[JIRA_CONNECTION_TEST] Testando conexão com endpoint {test_endpoint}")
            test_response = self._make_request("GET", test_endpoint)
            logger.info(f"[JIRA_CONNECTION_TEST] Conexão bem-sucedida! Resposta: {test_response.get('displayName', 'N/A')}")
        except Exception as e:
            logger.error(f"[JIRA_CONNECTION_TEST] Falha ao testar conexão: {str(e)}")
            # Retornar lista vazia em caso de erro na conexão
            return []
        
        # Buscar projetos com paginação
        start_at = 0
        max_results = 50
        all_projects = []
        
        try:
            while True:
                # Construir endpoint com parâmetros de paginação
                endpoint = f"/rest/api/3/project/search?startAt={start_at}&maxResults={max_results}"
                logger.info(f"[JIRA_FETCH_PROJECTS] Buscando projetos com: startAt={start_at}, maxResults={max_results}")
                
                # Fazer requisição
                response = self._make_request("GET", endpoint)
                
                # Verificar estrutura da resposta
                if "values" not in response:
                    logger.error(f"[JIRA_FETCH_PROJECTS] Resposta não contém campo 'values': {response}")
                    break
                
                projects = response.get("values", [])
                total = response.get("total", 0)
                
                logger.info(f"[JIRA_FETCH_PROJECTS] Obtidos {len(projects)} projetos de {total}")
                
                # Verificar primeiro projeto para debug
                if projects and len(projects) > 0:
                    first_project = projects[0]
                    logger.info(f"[JIRA_FETCH_PROJECTS] Exemplo de projeto: ID={first_project.get('id', 'N/A')}, Key={first_project.get('key', 'N/A')}, Nome={first_project.get('name', 'N/A')}")
                
                all_projects.extend(projects)
                
                if len(all_projects) >= total or len(projects) == 0:
                    break
                    
                start_at += max_results
        except Exception as e:
            logger.error(f"[JIRA_FETCH_PROJECTS] Erro ao buscar projetos: {str(e)}")
        
        logger.info(f"[JIRA_FETCH_PROJECTS] Total de projetos obtidos: {len(all_projects)}")
        
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
        
        # Usar exatamente o mesmo header de autorização que está funcionando
        # Este header foi testado e funciona corretamente
        auth_header = "Basic cm9saXZlaXJhQHdlZy5uZXQ6QVRBVFQzeEZmR0YwZG0xUzdSSHNReGFSTDZkNmZiaEZUMFNxSjZLbE9ScWRXQzg1M1Jlb3hFMUpnM0dSeXRUVTN4dG5McjdGVWg3WWFKZ2M1RDZwd3J5bjhQc3lHVDNrSklyRUlyVHpmNF9lMGJYLUdJdmxOOFIxanhyMV9GVGhLY1h3V1N0dU9VbE5ucEY2eFlhclhfWFpRb3RhTzlXeFhVaXlIWkdHTDFaMEx5cmJ4VzVyNVYwPUYxMDA3MDNF"
        
        # Cabeçalhos com o header de autorização que funciona
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": auth_header
        }
        
        # Log da requisição
        logger.info(f"[JIRA_REQUEST] {method} {url}")
        logger.info(f"[JIRA_REQUEST_AUTH_HEADER] Usando header de autorização fixo que funciona")
        
        # Log detalhado para depuração
        logger.info(f"[JIRA_REQUEST_DETAILED] Fazendo requisição {method} para {url}")
        
        # Nota: Este é um ajuste temporário até resolver o problema com a geração do header de autorização
        
        logger.info(f"[JIRA_REQUEST] {method} {url}")
        
        try:
            # Log da tentativa de requisição
            logger.info(f"[JIRA_REQUEST_ATTEMPT] Iniciando requisição {method} para {url}")
            
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")

            logger.info(f"[JIRA_RESPONSE] Status: {response.status_code}")
            
            # Log da resposta completa para diagnóstico quando for busca de projetos
            if "project/search" in url:
                try:
                    response_json = response.json()
                    logger.info(f"[JIRA_RESPONSE_FULL] Resposta completa para projetos: {response_json}")
                    
                    # Verificar se há mensagens de erro específicas na resposta
                    if "errorMessages" in response_json:
                        logger.error(f"[JIRA_ERROR_MESSAGES] {response_json['errorMessages']}")
                    if "errors" in response_json:
                        logger.error(f"[JIRA_ERRORS] {response_json['errors']}")
                        
                    # Verificar se a estrutura da resposta é a esperada
                    if "values" in response_json:
                        logger.info(f"[JIRA_VALUES] Quantidade de valores: {len(response_json['values'])}")
                    else:
                        logger.warning(f"[JIRA_WARNING] Campo 'values' não encontrado na resposta")
                        
                    # Verificar o total de projetos
                    if "total" in response_json:
                        logger.info(f"[JIRA_TOTAL] Total de projetos: {response_json['total']}")
                except Exception as e:
                    logger.error(f"[JIRA_RESPONSE_PARSE_ERROR] Erro ao processar resposta JSON: {str(e)}")
                    logger.error(f"[JIRA_RESPONSE_TEXT] Texto da resposta: {response.text[:1000]}")
            
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
                    
    def get_worklogs_updated_since(self, since_date: datetime) -> List[Dict[str, Any]]:
        """
        Obtém todos os worklogs atualizados desde uma determinada data.
        
        Args:
            since_date: Data a partir da qual buscar atualizações
            
        Returns:
            Lista de worklogs atualizados
        """
        import logging
        logger = logging.getLogger("jira_client.get_worklogs_updated_since")
        
        logger.info(f"[JIRA_WORKLOGS] Buscando worklogs atualizados desde {since_date}")
        
        # Converter a data para o formato esperado pelo Jira (epoch millis)
        import time
        since_epoch_millis = int(time.mktime(since_date.timetuple()) * 1000)
        
        # Endpoint para obter worklogs atualizados
        endpoint = f"/rest/api/3/worklog/updated?since={since_epoch_millis}"
        
        try:
            # Fazer a requisição para obter os IDs dos worklogs atualizados
            logger.info(f"[JIRA_WORKLOGS] Chamando endpoint: {endpoint}")
            response = self._make_request("GET", endpoint)
            
            # Verificar se a resposta contém o campo 'values'
            if "values" not in response:
                logger.warning(f"[JIRA_WORKLOGS] Resposta não contém campo 'values': {response}")
                return []
            
            # Extrair os IDs dos worklogs atualizados
            worklog_ids = [item.get("worklogId") for item in response.get("values", []) if item.get("worklogId")]
            
            if not worklog_ids:
                logger.info(f"[JIRA_WORKLOGS] Nenhum worklog atualizado desde {since_date}")
                return []
            
            logger.info(f"[JIRA_WORKLOGS] Encontrados {len(worklog_ids)} worklogs atualizados")
            
            # Buscar os detalhes de cada worklog
            all_worklogs = []
            for worklog_id in worklog_ids:
                try:
                    # Obter detalhes do worklog
                    worklog = self.get_worklog_by_id(worklog_id)
                    if worklog:
                        all_worklogs.append(worklog)
                except Exception as e:
                    logger.error(f"[JIRA_WORKLOGS] Erro ao obter detalhes do worklog {worklog_id}: {str(e)}")
            
            logger.info(f"[JIRA_WORKLOGS] Obtidos detalhes de {len(all_worklogs)} worklogs")
            return all_worklogs
            
        except Exception as e:
            logger.error(f"[JIRA_WORKLOGS] Erro ao buscar worklogs atualizados: {str(e)}")
            return []
    
    def get_worklog_by_id(self, worklog_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um worklog específico.
        
        Args:
            worklog_id: ID do worklog
            
        Returns:
            Dados do worklog
        """
        import logging
        logger = logging.getLogger("jira_client.get_worklog_by_id")
        
        logger.info(f"[JIRA_WORKLOG] Buscando detalhes do worklog {worklog_id}")
        
        # Primeiro, precisamos encontrar a issue associada ao worklog
        # Infelizmente, a API do Jira não permite buscar um worklog diretamente pelo ID
        # sem conhecer a issue associada
        
        # Vamos usar o endpoint de busca de worklogs
        endpoint = f"/rest/api/3/worklog/{worklog_id}"
        
        try:
            # Fazer a requisição para obter os detalhes do worklog
            logger.info(f"[JIRA_WORKLOG] Chamando endpoint: {endpoint}")
            worklog = self._make_request("GET", endpoint)
            
            # Verificar se obtivemos os dados do worklog
            if not worklog or not worklog.get("id"):
                logger.warning(f"[JIRA_WORKLOG] Resposta não contém dados válidos do worklog: {worklog}")
                return {}
            
            # Adicionar informações da issue ao worklog
            issue_id = worklog.get("issueId")
            if issue_id:
                try:
                    # Obter detalhes da issue
                    issue = self.get_issue(issue_id)
                    worklog["issueKey"] = issue.get("key")
                except Exception as e:
                    logger.error(f"[JIRA_WORKLOG] Erro ao obter detalhes da issue {issue_id}: {str(e)}")
            
            logger.info(f"[JIRA_WORKLOG] Detalhes do worklog {worklog_id} obtidos com sucesso")
            return worklog
            
        except Exception as e:
            logger.error(f"[JIRA_WORKLOG] Erro ao buscar detalhes do worklog {worklog_id}: {str(e)}")
            return {}
    
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
    
    def get_worklogs_updated_since(self, since_date: datetime) -> List[Dict[str, Any]]:
        """
        Obtém todos os worklogs atualizados desde uma determinada data.
        
        Args:
            since_date: Data a partir da qual buscar atualizações
            
        Returns:
            Lista de worklogs atualizados
        """
        logger.info(f"[JIRA_WORKLOGS] Buscando worklogs atualizados desde {since_date}")
        
        # Converter a data para o formato ISO 8601 esperado pela API do Jira
        since_str = since_date.strftime("%Y-%m-%dT%H:%M:%S.000%z")
        if not since_str.endswith('Z') and '+' not in since_str and '-' not in since_str[8:]:
            since_str += "+0000"
            
        logger.info(f"[JIRA_WORKLOGS] Data formatada: {since_str}")
        
        # Endpoint para buscar worklogs atualizados
        endpoint = f"/rest/api/3/worklog/updated?since={since_str}"
        
        try:
            # Fazer a requisição inicial
            response = self._make_request("GET", endpoint)
            
            # Verificar se temos worklogs
            if not response or "values" not in response:
                logger.warning(f"[JIRA_WORKLOGS] Resposta vazia ou sem valores: {response}")
                return []
                
            # Extrair IDs dos worklogs atualizados
            worklog_ids = [item.get("worklogId") for item in response.get("values", []) if item.get("worklogId")]
            
            logger.info(f"[JIRA_WORKLOGS] Encontrados {len(worklog_ids)} IDs de worklogs atualizados")
            
            # Se não temos IDs, retornar lista vazia
            if not worklog_ids:
                return []
                
            # Buscar detalhes dos worklogs em lotes de 100 (limite da API)
            all_worklogs = []
            for i in range(0, len(worklog_ids), 100):
                batch_ids = worklog_ids[i:i+100]
                
                # Endpoint para buscar detalhes dos worklogs
                worklogs_endpoint = f"/rest/api/3/worklog/list"
                
                # Dados para a requisição
                data = {"ids": batch_ids}
                
                # Fazer a requisição
                batch_response = self._make_request("POST", worklogs_endpoint, data)
                
                # Adicionar worklogs à lista
                if batch_response and isinstance(batch_response, list):
                    all_worklogs.extend(batch_response)
                    
            logger.info(f"[JIRA_WORKLOGS] Obtidos detalhes de {len(all_worklogs)} worklogs")
            return all_worklogs
            
        except Exception as e:
            logger.error(f"[JIRA_WORKLOGS] Erro ao buscar worklogs atualizados: {str(e)}")
            return []
    
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