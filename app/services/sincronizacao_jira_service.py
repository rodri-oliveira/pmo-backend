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
        """
        import logging
        logger = logging.getLogger("sincronizacoes_jira.importar_tudo")
        
        logger.info(f"[INICIO_SINC] Iniciando sincronização completa com o Jira para usuario_id={usuario_id}")
        logger.info(f"[CONFIG_JIRA] BASE_URL={self.jira_client.base_url}, USERNAME={self.jira_client.username}")
        
        from datetime import timezone
        # Registrar início da sincronização - usando datetime sem timezone
        # Como data_fim não pode ser NULL no banco de dados, usamos a mesma data de início
        data_atual = datetime.now()
        logger.info(f"[DATA] Criando registro com data_atual={data_atual}")
        
        # Criar dados para o registro de sincronização
        dados_sincronizacao = {
            "data_inicio": data_atual,
            "data_fim": data_atual,  # Usamos a mesma data de início e atualizamos depois
            "status": "PROCESSANDO",
            "mensagem": "Iniciando sincronização completa com o Jira",
            "quantidade_apontamentos_processados": 0
        }
        
        # Adicionar usuario_id apenas se for fornecido e não for None
        if usuario_id is not None:
            dados_sincronizacao["usuario_id"] = usuario_id
            
        sincronizacao = await self.sincronizacao_repository.create(dados_sincronizacao)
        logger.info(f"[REGISTRO] Sincronização criada com ID={sincronizacao.id}")
        
        try:
            resultado = self.jira_client.fetch_all_projects_issues_worklogs()
            await self.sincronizacao_repository.update(sincronizacao.id, {
                "data_fim": datetime.now(),
                "status": "SUCESSO",
                "mensagem": f"Sincronização total concluída. Projetos: {resultado['total_projects']}, Issues: {resultado['total_issues']}, Worklogs: {resultado['total_worklogs']}",
                "quantidade_apontamentos_processados": resultado['total_worklogs']
            })
            return {
                "status": "success",
                "message": f"Sincronização total concluída.",
                "projetos": resultado['total_projects'],
                "issues": resultado['total_issues'],
                "worklogs": resultado['total_worklogs']
            }
        except Exception as e:
            await self.sincronizacao_repository.update(sincronizacao.id, {
                "data_fim": datetime.now(),
                "status": "ERRO",
                "mensagem": f"Erro na sincronização total: {str(e)}",
                "quantidade_apontamentos_processados": 0
            })
            raise ValueError(f"Erro na sincronização total com o Jira: {str(e)}")
    
    # O método __init__ já foi definido acima
    
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
                worklog_data = self._extrair_dados_worklog(worklog)
                
                if worklog_data:
                    # Sincronizar no banco
                    await self.apontamento_repository.sync_jira_apontamento(worklog_data)
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
    
    def _extrair_dados_worklog(self, worklog: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extrai dados de um worklog do Jira para o formato do sistema.
        
        Args:
            worklog: Dados do worklog do Jira
            
        Returns:
            Optional[Dict[str, Any]]: Dados formatados para o apontamento ou None se inválido
        """
        try:
            # Extrair dados básicos
            worklog_id = str(worklog.get("id"))
            issue_id = worklog.get("issueId")
            
            # Se não tiver ID do worklog ou da issue, pular
            if not worklog_id or not issue_id:
                return None
            
            # Obter detalhes da issue
            issue_key = worklog.get("issueKey")
            if not issue_key:
                return None
            
            issue = self.jira_client.get_issue_details(issue_key)
            
            # Extrair dados do autor
            author = worklog.get("author", {})
            author_account_id = author.get("accountId")
            
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
