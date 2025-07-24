"""
Service para sincronização Jira com parâmetros de data flexíveis
Baseado no script sincronizacao_jira_corrigida.py
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from app.db.session import AsyncSessionLocal
from app.integrations.jira_client import JiraClient
from app.repositories.apontamento_repository import ApontamentoRepository
from app.repositories.secao_repository import SecaoRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.recurso_repository import RecursoRepository

logger = logging.getLogger(__name__)


class SincronizacaoJiraCorrigidaService:
    """Service para sincronização Jira com controle de período"""
    
    def __init__(self, session):
        self.session = session
        self.jira_client = JiraClient()
        self.apontamento_repo = ApontamentoRepository(session)
        self.secao_repo = SecaoRepository(session)
        self.projeto_repo = ProjetoRepository(session)
        self.recurso_repo = RecursoRepository(session)
        
        # Contadores para relatório
        self.stats = {
            'issues_processadas': 0,
            'apontamentos_criados': 0,
            'recursos_criados': 0,
            'recursos_atualizados': 0,
            'projetos_criados': 0,
            'projetos_atualizados': 0,
            'erros': 0
        }

    async def buscar_secao(self, jira_project_key: str) -> Optional[Any]:
        """
        Busca uma seção existente baseada no jira_project_key.
        NÃO CRIA novas seções - apenas busca existentes.
        """
        try:
            secao = await self.secao_repo.get_by_jira_project_key(jira_project_key)
            
            if secao:
                logger.info(f"[SECAO_FOUND] Seção encontrada: {secao.nome} (id={secao.id})")
                return secao
            else:
                logger.warning(f"[SECAO_NOT_FOUND] Seção não encontrada para {jira_project_key}")
                return None
            
        except Exception as e:
            logger.error(f"[SECAO_ERROR] Erro ao buscar seção {jira_project_key}: {str(e)}")
            return None

    async def upsert_recurso(self, assignee_data: Dict[str, Any]) -> Optional[Any]:
        """Busca ou cria um recurso baseado nos dados do assignee do Jira."""
        jira_user_id = assignee_data.get("accountId")
        email = assignee_data.get("emailAddress")
        nome = assignee_data.get("displayName")
        ativo = assignee_data.get("active", True)
        
        if not email:
            logger.warning(f"[RECURSO_SKIP] Assignee sem email: {nome}")
            return None
        
        try:
            # Buscar recurso existente
            recurso = await self.recurso_repo.get_by_jira_user_id(jira_user_id)
            if not recurso:
                recurso = await self.recurso_repo.get_by_email(email)
            
            if recurso:
                # Atualizar se necessário
                updates = {}
                if nome and recurso.nome != nome:
                    updates["nome"] = nome
                if email and recurso.email != email:
                    updates["email"] = email
                if jira_user_id and recurso.jira_user_id != jira_user_id:
                    updates["jira_user_id"] = jira_user_id
                if recurso.ativo != ativo:
                    updates["ativo"] = ativo
                
                if updates:
                    for key, value in updates.items():
                        setattr(recurso, key, value)
                    await self.session.commit()
                    await self.session.refresh(recurso)
                    self.stats['recursos_atualizados'] += 1
                    logger.info(f"[RECURSO_UPDATED] Recurso atualizado: {recurso.email} (id={recurso.id})")
                
                return recurso
            
            # Criar novo recurso
            recurso_data = {
                "nome": nome or email,
                "email": email,
                "jira_user_id": jira_user_id,
                "ativo": ativo
            }
            
            recurso = await self.recurso_repo.create(recurso_data)
            self.stats['recursos_criados'] += 1
            logger.info(f"[RECURSO_CREATED] Novo recurso criado: {recurso.email} (id={recurso.id})")
            
            return recurso
            
        except Exception as e:
            logger.error(f"[RECURSO_ERROR] Erro ao processar recurso: {str(e)}")
            return None

    async def upsert_projeto(self, issue_key: str, issue_summary: str, secao_id: int) -> Optional[Any]:
        """Busca ou cria um projeto baseado na issue do Jira."""
        try:
            # Buscar projeto existente
            projeto = await self.projeto_repo.get_by_jira_project_key(issue_key)
            
            if projeto:
                # Atualizar nome se mudou
                if issue_summary and projeto.nome != issue_summary:
                    projeto.nome = issue_summary
                    await self.session.commit()
                    await self.session.refresh(projeto)
                    self.stats['projetos_atualizados'] += 1
                    logger.info(f"[PROJETO_UPDATED] Projeto atualizado: {projeto.nome} (id={projeto.id})")
                
                return projeto
            
            # Buscar status padrão
            status_default = await self.projeto_repo.get_status_default()
            if not status_default:
                logger.error(f"[PROJETO_ERROR] Status padrão não encontrado")
                return None
            
            # Criar novo projeto
            projeto_data = {
                "nome": issue_summary or issue_key,
                "descricao": f"Projeto criado automaticamente para issue {issue_key}",
                "jira_project_key": issue_key,
                "secao_id": secao_id,
                "status_projeto_id": status_default.id,
                "ativo": True
            }
            
            projeto = await self.projeto_repo.create(projeto_data)
            self.stats['projetos_criados'] += 1
            logger.info(f"[PROJETO_CREATED] Novo projeto criado: {projeto.nome} (id={projeto.id})")
            
            return projeto
            
        except Exception as e:
            logger.error(f"[PROJETO_ERROR] Erro ao processar projeto {issue_key}: {str(e)}")
            return None

    async def sincronizar_periodo(
        self, 
        data_inicio: datetime, 
        data_fim: datetime,
        projetos: List[str] = None
    ) -> Dict[str, Any]:
        """
        Sincroniza worklogs do Jira para um período específico.
        
        Args:
            data_inicio: Data de início da sincronização
            data_fim: Data de fim da sincronização
            projetos: Lista de projetos para sincronizar (default: DTIN, SGI, TIN, SEG)
            
        Returns:
            Dicionário com estatísticas da sincronização
        """
        inicio_execucao = datetime.now()
        
        try:
            logger.info(f"[SYNC_START] Iniciando sincronização: {data_inicio.date()} até {data_fim.date()}")
            
            # Projetos padrão se não especificados
            if not projetos:
                projetos = ["DTIN", "SGI", "TIN", "SEG"]
            
            project_keys_str = ", ".join(projetos)
            
            # JQL com filtro de data nos worklogs
            jql = (
                f"project IN ({project_keys_str}) "
                f"AND worklogDate >= '{data_inicio.date()}' "
                f"AND worklogDate <= '{data_fim.date()}'"
            )
            
            logger.info(f"[JQL] Query: {jql}")
            
            # Buscar todas as issues com worklogs no período
            issues = self.jira_client.get_all_issues(
                jql, 
                fields=["key", "summary", "assignee", "worklog", "project"]
            )
            
            logger.info(f"[ISSUES] Encontradas {len(issues)} issues")
            
            for issue in issues:
                try:
                    await self._processar_issue(issue, data_inicio, data_fim)
                    self.stats['issues_processadas'] += 1
                    
                except Exception as e:
                    issue_key = issue.get("key", "NO_KEY")
                    logger.error(f"[ISSUE_ERROR] Erro ao processar issue {issue_key}: {str(e)}")
                    self.stats['erros'] += 1
                    continue
            
            # Commit final
            await self.session.commit()
            
            # Calcular tempo de execução
            tempo_execucao = datetime.now() - inicio_execucao
            tempo_str = str(tempo_execucao).split('.')[0]  # Remove microssegundos
            
            resultado = {
                "status": "success",
                "periodo": {
                    "inicio": data_inicio.date().isoformat(),
                    "fim": data_fim.date().isoformat()
                },
                "resultados": self.stats.copy(),
                "tempo_execucao": tempo_str
            }
            
            logger.info(f"[SYNC_SUCCESS] Sincronização concluída em {tempo_str}")
            return resultado
            
        except Exception as e:
            logger.error(f"[SYNC_ERROR] Erro na sincronização: {str(e)}")
            await self.session.rollback()
            
            tempo_execucao = datetime.now() - inicio_execucao
            tempo_str = str(tempo_execucao).split('.')[0]
            
            return {
                "status": "error",
                "periodo": {
                    "inicio": data_inicio.date().isoformat(),
                    "fim": data_fim.date().isoformat()
                },
                "resultados": self.stats.copy(),
                "tempo_execucao": tempo_str,
                "erro": str(e)
            }

    async def _processar_issue(self, issue: Dict[str, Any], data_inicio: datetime, data_fim: datetime):
        """Processa uma issue individual"""
        issue_key = issue.get("key", "")
        fields = issue.get("fields", {})
        
        logger.info(f"[ISSUE] Processando {issue_key}")
        
        # 1. Buscar seção existente (prefixo da issue)
        project_prefix = issue_key.split("-")[0] if "-" in issue_key else issue_key
        secao = await self.buscar_secao(project_prefix)
        if not secao:
            logger.error(f"[ISSUE_SKIP] Seção não encontrada para {issue_key} (prefix: {project_prefix})")
            return
        
        # 2. Upsert do projeto (issue = projeto)
        issue_summary = fields.get("summary", "").strip()
        projeto = await self.upsert_projeto(issue_key, issue_summary, secao.id)
        if not projeto:
            logger.error(f"[ISSUE_SKIP] Projeto não criado para {issue_key}")
            return
        
        # 3. Upsert do recurso (assignee)
        assignee = fields.get("assignee")
        if not assignee:
            logger.warning(f"[ISSUE_SKIP] Issue {issue_key} sem assignee")
            return
        
        recurso = await self.upsert_recurso(assignee)
        if not recurso:
            logger.error(f"[ISSUE_SKIP] Recurso não criado para {issue_key}")
            return
        
        # 4. Processar todos os worklogs da issue
        worklogs = self.jira_client.get_all_worklogs(issue_key)
        logger.info(f"[WORKLOGS] Issue {issue_key}: {len(worklogs)} worklogs")
        
        for worklog in worklogs:
            try:
                await self._processar_worklog(worklog, issue_key, recurso.id, projeto.id, data_inicio, data_fim)
            except Exception as e:
                wl_id = worklog.get("id", "NO_ID")
                logger.error(f"[WORKLOG_ERROR] Erro no worklog {wl_id}: {str(e)}")
                continue

    async def _processar_worklog(self, worklog: Dict[str, Any], issue_key: str, recurso_id: int, projeto_id: int, data_inicio: datetime, data_fim: datetime):
        """Processa um worklog individual"""
        worklog_id = worklog.get("id")
        if not worklog_id:
            logger.warning(f"[WORKLOG_SKIP] Worklog sem ID para issue {issue_key}")
            return
        
        # Verificar se o worklog está no período
        started_str = worklog.get("started", "")
        if not started_str:
            logger.warning(f"[WORKLOG_SKIP] Worklog {worklog_id} sem data de início")
            return
        
        try:
            # Parse da data do worklog
            started_dt = self._parse_jira_datetime(started_str)
            if not (data_inicio <= started_dt <= data_fim):
                return  # Worklog fora do período
            
            # Sincronizar apontamento
            await self.apontamento_repo.sync_apontamento(
                jira_worklog_id=int(worklog_id),
                recurso_id=recurso_id,
                projeto_id=projeto_id,
                data_apontamento=started_dt.date(),
                horas_apontadas=worklog.get("timeSpentSeconds", 0) / 3600,
                descricao=worklog.get("comment", {}).get("content", [{}])[0].get("content", [{}])[0].get("text", "") if worklog.get("comment") else ""
            )
            
            self.stats['apontamentos_criados'] += 1
            
        except Exception as e:
            logger.error(f"[WORKLOG_ERROR] Erro ao processar worklog {worklog_id}: {str(e)}")
            raise

    def _parse_jira_datetime(self, datetime_str: str) -> datetime:
        """Parse de datetime do Jira"""
        try:
            # Formato: 2024-07-23T14:30:00.000-0300
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1] + '+00:00'
            elif '+' in datetime_str[-6:] or '-' in datetime_str[-6:]:
                # Já tem timezone
                pass
            else:
                datetime_str += '+00:00'
            
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.error(f"[DATETIME_ERROR] Erro ao fazer parse de {datetime_str}: {str(e)}")
            return datetime.now()
