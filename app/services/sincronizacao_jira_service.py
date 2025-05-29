from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.jira_client import JiraClient
from app.repositories.apontamento_repository import ApontamentoRepository
from app.repositories.recurso_repository import RecursoRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.sincronizacao_jira_repository import SincronizacaoJiraRepository
from app.db.orm_models import FonteApontamento

class SincronizacaoJiraService:
    """Serviço para sincronização de dados com o Jira."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.jira_client = JiraClient()
        self.apontamento_repository = ApontamentoRepository(db)
        self.recurso_repository = RecursoRepository(db)
        self.projeto_repository = ProjetoRepository(db)
        self.sincronizacao_repository = SincronizacaoJiraRepository(db)

    async def sincronizar_tudo(self, usuario_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Sincroniza todos os dados do Jira (projetos, issues, worklogs).
        Simplificado para usar o método sincronizar_apontamentos que já está implementado.
        
        Args:
            usuario_id: ID do usuário que iniciou a sincronização (opcional)
            
        Returns:
            Dict[str, Any]: Resultado da sincronização
        """
        import logging
        logger = logging.getLogger("sincronizacoes_jira.importar_tudo")
        
        logger.info(f"[INICIO_SINC] Iniciando sincronização completa com o Jira para usuario_id={usuario_id}")
        
        # Verificar configurações do Jira
        logger.info(f"[JIRA_CONFIG] Base URL: {self.jira_client.base_url}")
        logger.info(f"[JIRA_CONFIG] Username: {self.jira_client.username}")
        if self.jira_client.api_token:
            token_preview = self.jira_client.api_token[:5] + "..." + self.jira_client.api_token[-5:] if len(self.jira_client.api_token) > 10 else "***"
            logger.info(f"[JIRA_CONFIG] API Token: {token_preview}")
        else:
            logger.error(f"[JIRA_CONFIG] API Token não definido!")
        
        # Testar conexão com o Jira antes de prosseguir
        try:
            logger.info(f"[JIRA_TEST] Testando conexão com o Jira")
            test_response = self.jira_client._make_request("GET", "/rest/api/3/myself")
            logger.info(f"[JIRA_TEST] Conexão com o Jira bem-sucedida! Usuário: {test_response.get('displayName', 'N/A')}")
        except Exception as e:
            logger.error(f"[JIRA_TEST_ERROR] Erro ao testar conexão com o Jira: {str(e)}")
            raise Exception(f"Erro ao testar conexão com o Jira: {str(e)}")
        
        # Em vez de tentar sincronizar projetos, issues e worklogs separadamente,
        # vamos usar o método sincronizar_apontamentos que já está implementado
        try:
            logger.info(f"[APONTAMENTOS_SYNC] Iniciando sincronização de apontamentos")
            result = await self.sincronizar_apontamentos(usuario_id)
            logger.info(f"[APONTAMENTOS_SYNC_RESULT] {result}")
            
            return {
                "status": "success",
                "message": "Sincronização completa concluída com sucesso",
                "data": result
            }
        except Exception as e:
            logger.error(f"[ERRO_SINC] Erro na sincronização completa: {str(e)}")
            raise ValueError(f"Erro na sincronização total com o Jira: {str(e)}")
    
    async def obter_sincronizacao(self, id: int):
        """
        Obtém uma sincronização pelo ID.
        
        Args:
            id: ID da sincronização
            
        Returns:
            Sincronização encontrada ou None
        """
        return await self.sincronizacao_repository.get(id)
    
    async def listar_sincronizacoes(self, skip: int = 0, limit: int = 50, status: Optional[str] = None, tipo_evento: Optional[str] = None) -> Dict[str, Any]:
        """
        Lista sincronizações Jira com paginação e filtros.
        Args:
            skip: Quantidade de registros a pular
            limit: Quantidade máxima de registros
            status: Filtro por status
            tipo_evento: Filtro por tipo de evento
        Returns:
            Dict contendo items, total, skip e limit
        """
        items, total = await self.sincronizacao_repository.list_with_pagination(skip=skip, limit=limit, status=status, tipo_evento=tipo_evento)
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def sincronizar_apontamentos(self, usuario_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Sincroniza apontamentos com o Jira.
        
        Args:
            usuario_id: ID do usuário que iniciou a sincronização (opcional)
            
        Returns:
            Dict[str, Any]: Resultado da sincronização
        """
        # Registrar início da sincronização
        # Como data_fim não pode ser NULL no banco de dados, usamos a mesma data de início
        data_atual = datetime.now()
        
        # Criar dados para o registro de sincronização
        dados_sincronizacao = {
            "data_inicio": data_atual,
            "data_fim": data_atual,  # Usamos a mesma data de início e atualizamos depois
            "status": "PROCESSANDO",
            "mensagem": "Iniciando sincronização com o Jira",
            "quantidade_apontamentos_processados": 0
        }
        
        # Adicionar usuario_id apenas se for fornecido e não for None
        if usuario_id is not None:
            dados_sincronizacao["usuario_id"] = usuario_id
            
        sincronizacao = await self.sincronizacao_repository.create(dados_sincronizacao)
        
        try:
            # Obter a última sincronização bem-sucedida
            ultima_sincronizacao = await self.sincronizacao_repository.get_last_successful()
            
            # Determinar a data desde a qual buscar atualizações
            since = ultima_sincronizacao.data_fim if ultima_sincronizacao else datetime.now() - timedelta(days=30)
            
            # Buscar worklogs atualizados
            worklogs = self.jira_client.get_worklogs_updated_since(since)
            
            # Processar os worklogs
            count = 0
            for worklog in worklogs:
                # Extrair dados do worklog
                worklog_data = await self._extrair_dados_worklog(worklog)
                
                if worklog_data:
                    # Sincronizar no banco
                    await self.apontamento_repository.sync_jira_apontamento(worklog_data["jira_worklog_id"], worklog_data)
                    count += 1
            
            # Atualizar registro de sincronização
            await self.sincronizacao_repository.update(sincronizacao.id, {
                "data_fim": datetime.now(),
                "status": "SUCESSO",
                "mensagem": f"Sincronização concluída com sucesso. {count} apontamentos processados.",
                "quantidade_apontamentos_processados": count
            })
            
            return {
                "status": "success",
                "message": f"Sincronização concluída com sucesso",
                "apontamentos_processados": count
            }
            
        except Exception as e:
            # Registrar falha
            await self.sincronizacao_repository.update(sincronizacao.id, {
                "data_fim": datetime.now(),
                "status": "ERRO",
                "mensagem": f"Erro na sincronização: {str(e)}",
                "quantidade_apontamentos_processados": 0
            })
            
            raise ValueError(f"Erro na sincronização com o Jira: {str(e)}")
    
    async def _extrair_dados_worklog(self, worklog: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extrai dados de um worklog do Jira para o formato do sistema.
        
        Args:
            worklog: Dados do worklog do Jira
            
        Returns:
            Optional[Dict[str, Any]]: Dados formatados para o apontamento ou None se inválido
        """
        import logging
        logger = logging.getLogger("sincronizacoes_jira.extrair_dados_worklog")
        
        try:
            # Extrair dados básicos
            worklog_id = str(worklog.get("id"))
            
            # Verificar se temos o ID do worklog
            if not worklog_id:
                logger.warning(f"[WORKLOG_EXTRACT] Worklog sem ID: {worklog}")
                return None
                
            # Extrair informações da issue
            issue_id = worklog.get("issueId")
            issue_key = worklog.get("issueKey")
            
            # Se não temos a chave da issue, tentar obtê-la do campo issueId
            if not issue_key and issue_id:
                logger.info(f"[WORKLOG_EXTRACT] Obtendo issue_key a partir do issue_id: {issue_id}")
                try:
                    # Tentar obter a issue pelo ID
                    issue_data = self.jira_client.get_issue(issue_id)
                    issue_key = issue_data.get("key")
                except Exception as e:
                    logger.error(f"[WORKLOG_EXTRACT] Erro ao obter issue pelo ID {issue_id}: {str(e)}")
            
            # Se ainda não temos a chave da issue, não podemos continuar
            if not issue_key:
                logger.warning(f"[WORKLOG_EXTRACT] Worklog sem issue_key: {worklog}")
                return None
                
            # Extrair dados do autor
            author = worklog.get("author", {})
            author_account_id = author.get("accountId")
            author_email = author.get("emailAddress")
            author_display_name = author.get("displayName")
            
            # Verificar se temos informações do autor
            if not author_account_id and not author_email:
                logger.warning(f"[WORKLOG_EXTRACT] Worklog sem informações do autor: {worklog}")
                return None
                
            # Buscar o recurso pelo jira_user_id ou email
            recurso = None
            if author_account_id:
                recurso = await self.recurso_repository.get_by_jira_user_id(author_account_id)
                
            if not recurso and author_email:
                recurso = await self.recurso_repository.get_by_email(author_email)
                
            # Se não encontramos o recurso, criar um novo
            if not recurso:
                logger.info(f"[WORKLOG_EXTRACT] Recurso não encontrado para {author_account_id}/{author_email}, criando novo")
                
                # Dados para criar o recurso
                recurso_data = {
                    "nome": author_display_name or author_email or "Usuário Jira",
                    "email": author_email or f"{author_account_id}@jira.weg.net",
                    "jira_user_id": author_account_id,
                    "ativo": True
                }
                
                try:
                    recurso = await self.recurso_repository.create(recurso_data)
                except Exception as e:
                    logger.error(f"[WORKLOG_EXTRACT] Erro ao criar recurso: {str(e)}")
                    return None
            
            # Buscar o projeto pelo jira_project_key
            # Extrair o project_key da issue_key (formato: PROJECT-123)
            project_key = issue_key.split('-')[0] if '-' in issue_key else None
            
            if not project_key:
                logger.warning(f"[WORKLOG_EXTRACT] Não foi possível extrair project_key de {issue_key}")
                return None
                
            projeto = await self.projeto_repository.get_by_jira_project_key(project_key)
            
            # Se não encontramos o projeto, criar um novo
            if not projeto:
                logger.info(f"[WORKLOG_EXTRACT] Projeto não encontrado para {project_key}, criando novo")
                
                # Buscar detalhes do projeto no Jira
                try:
                    projeto_jira = self.jira_client.get_project(project_key)
                    projeto_nome = projeto_jira.get("name") or f"Projeto {project_key}"
                except Exception as e:
                    logger.error(f"[WORKLOG_EXTRACT] Erro ao obter projeto do Jira: {str(e)}")
                    projeto_nome = f"Projeto {project_key}"
                
                # Buscar o status padrão para projetos
                status_projeto = await self.projeto_repository.get_status_default()
                
                if not status_projeto:
                    logger.error(f"[WORKLOG_EXTRACT] Não foi possível encontrar status padrão para projetos")
                    return None
                
                # Dados para criar o projeto
                projeto_data = {
                    "nome": projeto_nome,
                    "jira_project_key": project_key,
                    "status_projeto_id": status_projeto.id,
                    "ativo": True
                }
                
                try:
                    projeto = await self.projeto_repository.create(projeto_data)
                except Exception as e:
                    logger.error(f"[WORKLOG_EXTRACT] Erro ao criar projeto: {str(e)}")
                    return None
            
            # Extrair horas apontadas
            # O campo timeSpentSeconds contém o tempo gasto em segundos
            time_spent_seconds = worklog.get("timeSpentSeconds")
            
            if not time_spent_seconds:
                logger.warning(f"[WORKLOG_EXTRACT] Worklog sem timeSpentSeconds: {worklog}")
                return None
                
            # Converter segundos para horas (com precisão de 2 casas decimais)
            horas_apontadas = round(time_spent_seconds / 3600, 2)
            
            # Extrair data e hora do apontamento
            started = worklog.get("started")  # Formato ISO: 2023-05-29T12:00:00.000+0000
            
            if not started:
                logger.warning(f"[WORKLOG_EXTRACT] Worklog sem data de início: {worklog}")
                return None
                
            # Converter string ISO para datetime
            from datetime import datetime
            import dateutil.parser
            
            try:
                data_hora_inicio = dateutil.parser.parse(started)
                # Remover timezone para compatibilidade com o banco
                if data_hora_inicio.tzinfo:
                    data_hora_inicio = data_hora_inicio.replace(tzinfo=None)
                    
                # Extrair apenas a data para data_apontamento
                data_apontamento = data_hora_inicio.date()
            except Exception as e:
                logger.error(f"[WORKLOG_EXTRACT] Erro ao converter data: {str(e)}")
                return None
            
            # Extrair descrição do worklog
            descricao = worklog.get("comment") or ""
            
            # Se o comentário for um objeto complexo (como em alguns formatos do Jira)
            if isinstance(descricao, dict):
                # Tentar extrair o texto do objeto de comentário
                if "content" in descricao:
                    try:
                        # Extrair texto do formato Atlassian Document Format
                        texto = []
                        for item in descricao.get("content", []):
                            if item.get("type") == "paragraph":
                                for content in item.get("content", []):
                                    if content.get("type") == "text":
                                        texto.append(content.get("text", ""))
                        descricao = " ".join(texto)
                    except Exception as e:
                        logger.error(f"[WORKLOG_EXTRACT] Erro ao extrair texto do comentário: {str(e)}")
                        descricao = "Comentário em formato não suportado"
            
            # Montar o objeto de dados para o apontamento
            apontamento_data = {
                "jira_worklog_id": worklog_id,
                "recurso_id": recurso.id,
                "projeto_id": projeto.id,
                "jira_issue_key": issue_key,
                "data_hora_inicio_trabalho": data_hora_inicio,
                "data_apontamento": data_apontamento,
                "horas_apontadas": horas_apontadas,
                "descricao": descricao,
                "fonte_apontamento": "JIRA",
                "data_sincronizacao_jira": datetime.now(),
                "data_criacao": datetime.now(),
                "data_atualizacao": datetime.now()
            }
            
            logger.info(f"[WORKLOG_EXTRACT] Dados extraídos com sucesso para worklog {worklog_id}")
            return apontamento_data
            
        except Exception as e:
            logger.error(f"[WORKLOG_EXTRACT] Erro ao extrair dados do worklog: {str(e)}")
            # Logar o worklog para diagnóstico
            logger.error(f"[WORKLOG_EXTRACT] Worklog problemático: {worklog}")
            return None
            
            if not author_account_id:
                return None
            
            # Extrair outros dados necessários do worklog
            # ... (código para extrair outros dados necessários)
            
            return {
                "jira_worklog_id": worklog_id,
                "issue_id": issue_id,
                "issue_key": issue_key,
                "author_account_id": author_account_id
            }
            
        except Exception as e:
            # Log detalhado do erro
            print(f"Erro ao extrair dados do worklog: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status: {e.response.status_code}, Resposta: {e.response.text}")
            return None
    
    async def _sincronizar_projeto(self, projeto: Dict[str, Any]) -> None:
        """
        Sincroniza um projeto do Jira com o banco de dados local.
        
        Args:
            projeto: Dados do projeto do Jira
        """
        import logging
        logger = logging.getLogger("sincronizacoes_jira.sincronizar_projeto")
        
        try:
            # Extrair dados básicos do projeto
            project_key = projeto.get("key")
            project_name = projeto.get("name")
            
            if not project_key or not project_name:
                logger.warning(f"[PROJETO_SYNC] Projeto sem key ou name: {projeto}")
                return
            
            logger.info(f"[PROJETO_SYNC] Sincronizando projeto {project_key}: {project_name}")
            
            # Verificar se o projeto já existe no banco
            projeto_existente = await self.projeto_repository.get_by_jira_project_key(project_key)
            
            if projeto_existente:
                logger.info(f"[PROJETO_SYNC] Projeto {project_key} já existe no banco, atualizando")
                
                # Atualizar dados do projeto
                await self.projeto_repository.update(projeto_existente.id, {
                    "nome": project_name,
                    "data_atualizacao": datetime.now()
                })
            else:
                logger.info(f"[PROJETO_SYNC] Projeto {project_key} não existe no banco, criando")
                
                # Buscar o status padrão para projetos
                status_projeto = await self.projeto_repository.get_status_default()
                
                if not status_projeto:
                    logger.error(f"[PROJETO_SYNC] Não foi possível encontrar status padrão para projetos")
                    return
                
                # Criar o projeto no banco
                await self.projeto_repository.create({
                    "nome": project_name,
                    "jira_project_key": project_key,
                    "status_projeto_id": status_projeto.id,
                    "ativo": True,
                    "data_criacao": datetime.now(),
                    "data_atualizacao": datetime.now()
                })
                
            logger.info(f"[PROJETO_SYNC] Projeto {project_key} sincronizado com sucesso")
            
        except Exception as e:
            logger.error(f"[PROJETO_SYNC] Erro ao sincronizar projeto {projeto.get('key', 'N/A')}: {str(e)}")
            # Não propagar a exceção para não interromper o processo de sincronização
    
    async def _sincronizar_issue(self, issue: Dict[str, Any]) -> None:
        """
        Sincroniza uma issue do Jira com o banco de dados local.
        
        Args:
            issue: Dados da issue do Jira
        """
        import logging
        logger = logging.getLogger("sincronizacoes_jira.sincronizar_issue")
        
        try:
            # Extrair dados básicos da issue
            issue_id = issue.get("id")
            issue_key = issue.get("key")
            
            if not issue_id or not issue_key:
                logger.warning(f"[ISSUE_SYNC] Issue sem id ou key: {issue}")
                return
            
            logger.info(f"[ISSUE_SYNC] Sincronizando issue {issue_key}")
            
            # Como não temos uma tabela específica para issues, apenas registramos o log
            # Em uma implementação completa, poderíamos criar uma tabela para issues
            
            logger.info(f"[ISSUE_SYNC] Issue {issue_key} sincronizada com sucesso")
            
        except Exception as e:
            logger.error(f"[ISSUE_SYNC] Erro ao sincronizar issue {issue.get('key', 'N/A')}: {str(e)}")
            # Não propagar a exceção para não interromper o processo de sincronização
    
    async def _sincronizar_worklog(self, worklog: Dict[str, Any]) -> None:
        """
        Sincroniza um worklog do Jira com o banco de dados local.
        
        Args:
            worklog: Dados do worklog do Jira
        """
        import logging
        logger = logging.getLogger("sincronizacoes_jira.sincronizar_worklog")
        
        try:
            # Extrair dados básicos do worklog
            worklog_id = worklog.get("id")
            
            if not worklog_id:
                logger.warning(f"[WORKLOG_SYNC] Worklog sem id: {worklog}")
                return
            
            logger.info(f"[WORKLOG_SYNC] Sincronizando worklog {worklog_id}")
            
            # Extrair dados do worklog para o formato do sistema
            worklog_data = await self._extrair_dados_worklog(worklog)
            
            if not worklog_data:
                logger.warning(f"[WORKLOG_SYNC] Não foi possível extrair dados do worklog {worklog_id}")
                return
            
            # Sincronizar o worklog no banco
            await self.apontamento_repository.sync_jira_apontamento(worklog_data["jira_worklog_id"], worklog_data)
            
            logger.info(f"[WORKLOG_SYNC] Worklog {worklog_id} sincronizado com sucesso")
            
        except Exception as e:
            logger.error(f"[WORKLOG_SYNC] Erro ao sincronizar worklog {worklog.get('id', 'N/A')}: {str(e)}")
            # Não propagar a exceção para não interromper o processo de sincronização
            
    async def testar_conexao_jira(self) -> Dict[str, Any]:
        """
        Testa a conexão com o Jira e retorna informações detalhadas.
        
        Returns:
            Dict[str, Any]: Resultado do teste de conexão
        """
        import logging
        logger = logging.getLogger("sincronizacoes_jira.testar_conexao")
        
        resultado = {
            "status": "success",
            "detalhes": {}
        }
        
        # 1. Verificar configurações
        logger.info("[JIRA_TEST] Verificando configurações do Jira")
        resultado["detalhes"]["configuracoes"] = {
            "base_url": self.jira_client.base_url,
            "username": self.jira_client.username,
            "api_token": "***" if self.jira_client.api_token else None
        }
        
        if not self.jira_client.api_token:
            resultado["status"] = "error"
            resultado["detalhes"]["configuracoes"]["erro"] = "API Token não definido"
            return resultado
        
        # 2. Testar busca de projetos (endpoint principal)
        logger.info("[JIRA_TEST] Testando busca de projetos com o endpoint /rest/api/3/project/search")
        try:
            # Usar o endpoint de busca de projetos com limite de 1 projeto
            endpoint = "/rest/api/3/project/search?maxResults=1"
            projetos = self.jira_client._make_request("GET", endpoint)
            
            resultado["detalhes"]["projetos"] = {
                "sucesso": True,
                "total": projetos.get("total", 0),
                "exemplo": None
            }
            
            # Verificar se há projetos
            if projetos.get("values") and len(projetos["values"]) > 0:
                primeiro_projeto = projetos["values"][0]
                resultado["detalhes"]["projetos"]["exemplo"] = {
                    "id": primeiro_projeto.get("id"),
                    "key": primeiro_projeto.get("key"),
                    "name": primeiro_projeto.get("name")
                }
        except Exception as e:
            resultado["status"] = "error"
            resultado["detalhes"]["projetos"] = {
                "sucesso": False,
                "erro": str(e)
            }
            return resultado
        
        # 3. Testar busca de projetos
        logger.info("[JIRA_TEST] Testando busca de projetos")
        try:
            # Usar o endpoint de busca de projetos com limite de 1 projeto
            endpoint = "/rest/api/3/project/search?maxResults=1"
            projetos = self.jira_client._make_request("GET", endpoint)
            
            resultado["detalhes"]["projetos"] = {
                "sucesso": True,
                "total": projetos.get("total", 0),
                "exemplo": None
            }
            
            # Verificar se há projetos
            if projetos.get("values") and len(projetos["values"]) > 0:
                primeiro_projeto = projetos["values"][0]
                resultado["detalhes"]["projetos"]["exemplo"] = {
                    "id": primeiro_projeto.get("id"),
                    "key": primeiro_projeto.get("key"),
                    "name": primeiro_projeto.get("name")
                }
        except Exception as e:
            resultado["status"] = "error"
            resultado["detalhes"]["projetos"] = {
                "sucesso": False,
                "erro": str(e)
            }
            return resultado
        
        # 4. Testar busca de worklogs recentes
        logger.info("[JIRA_TEST] Testando busca de worklogs recentes")
        try:
            # Usar o endpoint de busca de worklogs atualizados nos últimos 7 dias
            from datetime import datetime, timedelta
            since_date = datetime.now() - timedelta(days=7)
            worklogs = self.jira_client.get_worklogs_updated_since(since_date)
            
            resultado["detalhes"]["worklogs"] = {
                "sucesso": True,
                "total": len(worklogs),
                "exemplo": None
            }
            
            # Verificar se há worklogs
            if worklogs and len(worklogs) > 0:
                primeiro_worklog = worklogs[0]
                resultado["detalhes"]["worklogs"]["exemplo"] = {
                    "id": primeiro_worklog.get("id"),
                    "issueId": primeiro_worklog.get("issueId"),
                    "issueKey": primeiro_worklog.get("issueKey"),
                    "author": primeiro_worklog.get("author", {}).get("displayName")
                }
        except Exception as e:
            resultado["status"] = "error"
            resultado["detalhes"]["worklogs"] = {
                "sucesso": False,
                "erro": str(e)
            }
        
        return resultado
