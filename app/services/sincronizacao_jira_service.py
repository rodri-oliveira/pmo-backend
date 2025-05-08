from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.integrations.jira_client import JiraClient
from app.repositories.apontamento_repository import ApontamentoRepository
from app.repositories.recurso_repository import RecursoRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.sincronizacao_jira_repository import SincronizacaoJiraRepository
from app.db.orm_models import FonteApontamento

class SincronizacaoJiraService:
    """Serviço para sincronização de dados com o Jira."""
    
    def __init__(self, db: Session):
        self.db = db
        self.jira_client = JiraClient()
        self.apontamento_repository = ApontamentoRepository(db)
        self.recurso_repository = RecursoRepository(db)
        self.projeto_repository = ProjetoRepository(db)
        self.sincronizacao_repository = SincronizacaoJiraRepository(db)
    
    def sincronizar_apontamentos(self, usuario_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Sincroniza apontamentos com o Jira.
        
        Args:
            usuario_id: ID do usuário que iniciou a sincronização (opcional)
            
        Returns:
            Dict[str, Any]: Resultado da sincronização
        """
        # Registrar início da sincronização
        sincronizacao = self.sincronizacao_repository.create({
            "data_inicio": datetime.utcnow(),
            "data_fim": None,  # Será atualizado ao final
            "status": "PROCESSANDO",
            "mensagem": "Iniciando sincronização com o Jira",
            "quantidade_apontamentos_processados": 0,
            "usuario_id": usuario_id
        })
        
        try:
            # Obter a última sincronização bem-sucedida
            ultima_sincronizacao = self.sincronizacao_repository.get_last_successful()
            
            # Determinar a data desde a qual buscar atualizações
            since = ultima_sincronizacao.data_fim if ultima_sincronizacao else datetime.utcnow() - timedelta(days=30)
            
            # Buscar worklogs atualizados
            worklogs = self.jira_client.get_worklogs_updated_since(since)
            
            # Processar os worklogs
            count = 0
            for worklog in worklogs:
                # Extrair dados do worklog
                worklog_data = self._extrair_dados_worklog(worklog)
                
                if worklog_data:
                    # Sincronizar no banco
                    self.apontamento_repository.sync_jira_apontamento(worklog_data)
                    count += 1
            
            # Atualizar registro de sincronização
            self.sincronizacao_repository.update(sincronizacao.id, {
                "data_fim": datetime.utcnow(),
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
            self.sincronizacao_repository.update(sincronizacao.id, {
                "data_fim": datetime.utcnow(),
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