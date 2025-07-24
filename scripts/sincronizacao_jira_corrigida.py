"""
Sincronização JIRA Corrigida - Versão Híbrida
Baseada no script antigo que funcionava, mas com correções para o esquema atual.

REGRAS DE NEGÓCIO:
1. Jira Project (DTIN) → secao.jira_project_key
2. Jira Issue (DTIN-7183) → projeto.jira_project_key  
3. Jira Assignee → recurso.jira_user_id
4. Cada Jira Worklog → Um apontamento separado

MELHORIAS:
- Upsert robusto de seção, recurso e projeto
- Validações de campos obrigatórios
- Transações seguras
- Logs detalhados para diagnóstico
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.services.sincronizacao_jira_service import SincronizacaoJiraService
from app.db.session import AsyncSessionLocal
from app.integrations.jira_client import JiraClient
from app.repositories.apontamento_repository import ApontamentoRepository
from app.repositories.secao_repository import SecaoRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.recurso_repository import RecursoRepository

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sincronizacao_jira_corrigida.log')
    ]
)
logger = logging.getLogger(__name__)

# Data inicial padrão para carga completa
DEFAULT_START_DATE = datetime(2024, 8, 1)

def extract_comment_text(comment):
    """Extrai texto do comentário JIRA"""
    if not comment or "content" not in comment:
        return None
    for block in comment["content"]:
        for frag in block.get("content", []):
            if "text" in frag:
                return frag["text"]
    return None

class SincronizacaoJiraCorrigida:
    """Serviço de sincronização JIRA corrigido"""
    
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
            'secoes_criadas': 0,
            'erros': 0
        }

    async def upsert_secao(self, jira_project_key: str) -> Optional[Any]:
        """
        Busca ou cria uma seção baseada no jira_project_key.
        
        Args:
            jira_project_key: Chave do projeto Jira (ex: "DTIN", "SGI")
            
        Returns:
            Objeto seção ou None se erro
        """
        try:
            # Buscar seção existente
            secao = await self.secao_repo.get_by_jira_project_key(jira_project_key)
            
            if secao:
                logger.info(f"[SECAO_FOUND] Seção encontrada: {secao.nome} (id={secao.id})")
                return secao
            
            # Criar nova seção
            secao_data = {
                "nome": f"Seção {jira_project_key}",
                "jira_project_key": jira_project_key,
                "descricao": f"Seção criada automaticamente para projeto Jira {jira_project_key}",
                "ativo": True
            }
            
            secao = await self.secao_repo.create(secao_data)
            self.stats['secoes_criadas'] += 1
            logger.info(f"[SECAO_CREATED] Nova seção criada: {secao.nome} (id={secao.id})")
            
            return secao
            
        except Exception as e:
            logger.error(f"[SECAO_ERROR] Erro ao processar seção {jira_project_key}: {str(e)}")
            return None

    async def upsert_recurso(self, assignee_data: Dict[str, Any]) -> Optional[Any]:
        """
        Busca ou cria um recurso baseado nos dados do assignee do Jira.
        
        Args:
            assignee_data: Dados do assignee do Jira
            
        Returns:
            Objeto recurso ou None se erro
        """
        try:
            jira_user_id = assignee_data.get("accountId")
            email = assignee_data.get("emailAddress")
            nome = assignee_data.get("displayName")
            ativo = assignee_data.get("active", True)
            
            # Email é obrigatório no schema
            if not email:
                logger.warning(f"[RECURSO_SKIP] Assignee sem email: {jira_user_id}")
                return None
            
            recurso = None
            
            # Buscar por jira_user_id primeiro
            if jira_user_id:
                recurso = await self.recurso_repo.get_by_jira_user_id(jira_user_id)
            
            # Se não encontrou, buscar por email
            if not recurso:
                recurso = await self.recurso_repo.get_by_email(email)
            
            if recurso:
                # Atualizar dados se necessário
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
                "nome": nome or email,  # Usar email como fallback
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
        """
        Busca ou cria um projeto baseado na issue do Jira.
        
        Args:
            issue_key: Chave da issue (ex: "DTIN-7183")
            issue_summary: Resumo da issue
            secao_id: ID da seção
            
        Returns:
            Objeto projeto ou None se erro
        """
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

    async def processar_periodo(self, data_inicio: datetime, data_fim: datetime):
        """
        Processa worklogs do Jira de data_inicio até data_fim com upserts robustos.
        """
        logger.info(f"[INICIO] Processando período: {data_inicio.date()} até {data_fim.date()}")
        
        try:
            # Projetos Jira para sincronizar
            project_keys = ["SEG", "SGI", "DTIN", "TIN"]
            project_keys_str = ", ".join(project_keys)
            
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
            
            # Relatório final
            logger.info("=" * 60)
            logger.info("RELATÓRIO DE SINCRONIZAÇÃO")
            logger.info("=" * 60)
            for key, value in self.stats.items():
                logger.info(f"{key.upper()}: {value}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"[ERRO_GERAL] Erro na sincronização: {str(e)}")
            await self.session.rollback()
            raise

    async def _processar_issue(self, issue: Dict[str, Any], data_inicio: datetime, data_fim: datetime):
        """Processa uma issue individual"""
        issue_key = issue.get("key", "")
        fields = issue.get("fields", {})
        
        logger.info(f"[ISSUE] Processando {issue_key}")
        
        # 1. Determinar seção (prefixo da issue)
        project_prefix = issue_key.split("-")[0] if "-" in issue_key else issue_key
        secao = await self.upsert_secao(project_prefix)
        if not secao:
            logger.error(f"[ISSUE_SKIP] Seção não encontrada para {issue_key}")
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
        wl_id_str = worklog.get("id")
        if not wl_id_str:
            logger.warning(f"[WORKLOG_SKIP] Worklog sem ID para {issue_key}")
            return
        
        # Parsing de datas
        def parse_dt(s): 
            return datetime.fromisoformat(s[:-6]) if s else None
        
        dt_created = parse_dt(worklog.get("created"))
        dt_updated = parse_dt(worklog.get("updated"))
        dt_started = parse_dt(worklog.get("started"))
        
        # Validar período
        if not dt_started or dt_started < data_inicio or dt_started > data_fim:
            logger.debug(f"[WORKLOG_SKIP] Worklog {wl_id_str} fora do período")
            return
        
        # Calcular horas
        time_spent_seconds = worklog.get("timeSpentSeconds", 0)
        horas = time_spent_seconds / 3600
        
        # Validar horas
        if horas <= 0 or horas > 24:
            logger.warning(f"[WORKLOG_SKIP] Worklog {wl_id_str}: horas inválidas ({horas})")
            return
        
        # Dados do apontamento
        apontamento_data = {
            "recurso_id": recurso_id,
            "projeto_id": projeto_id,
            "jira_issue_key": issue_key,
            "data_hora_inicio_trabalho": dt_started,
            "data_apontamento": dt_started.date(),
            "horas_apontadas": horas,
            "descricao": extract_comment_text(worklog.get("comment")),
            "fonte_apontamento": "JIRA",
            "data_criacao": dt_created or datetime.now(),
            "data_atualizacao": dt_updated or datetime.now(),
            "data_sincronizacao_jira": datetime.now(),
        }
        
        # Criar/atualizar apontamento
        await self.apontamento_repo.sync_jira_apontamento(wl_id_str, apontamento_data)
        self.stats['apontamentos_criados'] += 1
        logger.debug(f"[APONTAMENTO] Criado para worklog {wl_id_str}: {horas}h")

async def processar_periodo(data_inicio: datetime, data_fim: datetime):
    """Função principal para processar um período"""
    async with AsyncSessionLocal() as session:
        sincronizador = SincronizacaoJiraCorrigida(session)
        await sincronizador.processar_periodo(data_inicio, data_fim)

async def carga_completa():
    """Executa carga completa desde 01/08/2024"""
    data_inicio = DEFAULT_START_DATE
    data_fim = datetime.now()
    logger.info(f"[CARGA_COMPLETA] {data_inicio.date()} até {data_fim.date()}")
    await processar_periodo(data_inicio, data_fim)

async def carga_personalizada(start_str: str, end_str: str):
    """Executa carga personalizada"""
    data_inicio = datetime.strptime(start_str, "%Y-%m-%d")
    data_fim = datetime.strptime(end_str, "%Y-%m-%d")
    logger.info(f"[CARGA_PERSONALIZADA] {data_inicio.date()} até {data_fim.date()}")
    await processar_periodo(data_inicio, data_fim)

async def rotina_mensal():
    """Executa rotina mensal (mês anterior)"""
    hoje = datetime.now()
    primeiro_dia_mes_anterior = hoje.replace(day=1) - timedelta(days=1)
    primeiro_dia_mes_anterior = primeiro_dia_mes_anterior.replace(day=1)
    ultimo_dia_mes_anterior = hoje.replace(day=1) - timedelta(days=1)
    
    logger.info(f"[ROTINA_MENSAL] {primeiro_dia_mes_anterior.date()} até {ultimo_dia_mes_anterior.date()}")
    await processar_periodo(primeiro_dia_mes_anterior, ultimo_dia_mes_anterior)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 3:
        # Período personalizado: python script.py 2024-08-01 2024-08-31
        asyncio.run(carga_personalizada(sys.argv[1], sys.argv[2]))
    elif len(sys.argv) == 2 and sys.argv[1] == "mensal":
        # Rotina mensal: python script.py mensal
        asyncio.run(rotina_mensal())
    else:
        # Carga completa: python script.py
        asyncio.run(carga_completa())
