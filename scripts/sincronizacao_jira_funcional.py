"""
Sincronização JIRA Funcional - Baseado no script que funcionava
Com melhorias de hierarquia, campos adicionais e upserts robustos.

REGRAS DE NEGÓCIO:
1. Jira Project (DTIN) → secao.jira_project_key
2. Jira Issue (DTIN-7183) → projeto.jira_project_key  
3. Jira Assignee → recurso.jira_user_id
4. Cada Jira Worklog → Um apontamento separado
5. Hierarquia: parent/child preservada nos apontamentos

MELHORIAS:
- Upsert robusto de seção, recurso e projeto
- Campos adicionais: created, status, customfield_10020
- Hierarquia Jira preservada
- Transações seguras
- Logs detalhados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dateutil import parser

from app.db.session import AsyncSessionLocal
from app.integrations.jira_client import JiraClient
from app.repositories.apontamento_repository import ApontamentoRepository
from app.repositories.secao_repository import SecaoRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.recurso_repository import RecursoRepository
from app.db.orm_models import FonteApontamento

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sincronizacao_jira_funcional.log')
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

class SincronizacaoJiraFuncional:
    """Serviço de sincronização JIRA funcional com hierarquia"""
    
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
            logger.info(f"[SECAO_UPSERT] Iniciando upsert para projeto Jira: {jira_project_key}")
            
            # Mapeamento correto: DTIN (Jira) → TIN (Seção)
            secao_key = jira_project_key
            if jira_project_key == "DTIN":
                secao_key = "TIN"
                logger.info(f"[SECAO_MAPEAMENTO] DTIN → TIN")
            
            logger.info(f"[SECAO_BUSCA] Buscando seção com chave: {secao_key}")
            
            # Buscar seção existente
            secao = await self.secao_repo.get_by_jira_project_key(secao_key)
            
            if secao:
                logger.info(f"[SECAO_FOUND] Seção encontrada: {secao.nome} (id={secao.id})")
                return secao
            
            logger.info(f"[SECAO_CREATE] Seção não encontrada, criando nova seção para: {secao_key}")
            
            # Criar nova seção
            secao_data = {
                "nome": f"Seção {secao_key}",
                "jira_project_key": secao_key,
                "descricao": f"Seção criada automaticamente para projeto Jira {jira_project_key}",
                "ativo": True
            }
            
            logger.info(f"[SECAO_DATA] Dados da seção: {secao_data}")
            
            secao = await self.secao_repo.create(secao_data)
            self.stats['secoes_criadas'] += 1
            logger.info(f"[SECAO_CREATED] Nova seção criada: {secao.nome} (id={secao.id})")
            
            return secao
            
        except Exception as e:
            logger.error(f"[SECAO_ERROR] Erro ao processar seção {jira_project_key}: {str(e)}")
            logger.error(f"[SECAO_ERROR] Traceback: ", exc_info=True)
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

    async def upsert_projeto(self, issue_key: str, issue_summary: str, secao_id: int, fields: Dict[str, Any] = None) -> Optional[Any]:
        """
        Busca ou cria um projeto baseado na issue do Jira com campos adicionais.
        
        Args:
            issue_key: Chave da issue (ex: "DTIN-7183")
            issue_summary: Resumo da issue
            secao_id: ID da seção
            fields: Campos adicionais do Jira (created, status, customfield_10020)
            
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
            
            # ✅ EXTRAIR CAMPOS ADICIONAIS DO JIRA
            data_criacao = datetime.now()
            start_date = None
            jira_status = None
            
            if fields:
                # 1. Data de criação real do Jira
                created_date = fields.get('created')
                if created_date:
                    try:
                        data_criacao = parser.parse(created_date)
                        if data_criacao.tzinfo is not None:
                            data_criacao = data_criacao.replace(tzinfo=None)
                        logger.info(f"[PROJETO] Data criação Jira: {data_criacao}")
                    except Exception as e:
                        logger.warning(f"[PROJETO] Erro ao parsear created: {e}")
                
                # 2. Status do Jira
                status_data = fields.get('status', {})
                jira_status = status_data.get('name')
                if jira_status:
                    logger.info(f"[PROJETO] Status Jira: {jira_status}")
                
                # 3. StartDate do Sprint (customfield_10020)
                sprint_data = fields.get('customfield_10020', [])
                if sprint_data and len(sprint_data) > 0:
                    start_date_str = sprint_data[0].get('startDate')
                    if start_date_str:
                        try:
                            parsed_date = parser.parse(start_date_str)
                            if parsed_date.tzinfo is not None:
                                parsed_date = parsed_date.replace(tzinfo=None)
                            start_date = parsed_date.date()
                            logger.info(f"[PROJETO] Start date Sprint: {start_date}")
                        except Exception as e:
                            logger.warning(f"[PROJETO] Erro ao parsear startDate: {e}")
            
            # Criar novo projeto com dados completos
            projeto_data = {
                "nome": issue_summary or issue_key,
                "jira_project_key": issue_key,
                "secao_id": secao_id,
                "status_projeto_id": status_default.id,
                "ativo": True,
                "data_criacao": data_criacao,
                "data_inicio_prevista": start_date,  # ✅ CORRIGIDO: usar data_inicio_prevista
                "descricao": f"Status Jira: {jira_status}" if jira_status else None  # ✅ CORRIGIDO: usar descricao
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
            # Projetos Jira para sincronizar (chaves dos projetos)
            # IMPORTANTE: Usar as chaves corretas dos projetos no Jira
            project_keys = [
                "SEG",   # Seção Segurança
                "SGI",   # Seção Suporte Global Infraestrutura
                "DTIN"   # Departamento de TI (mapeado para TIN)
            ]
            
            logger.info(f"[PROJETOS] Sincronizando projetos: {project_keys}")
            project_keys_str = ', '.join([f'"{key}"' for key in project_keys])
            
            # JQL com filtro de data nos worklogs
            jql = (
                f"project IN ({project_keys_str}) "
                f"AND worklogDate >= '{data_inicio.date()}' "
                f"AND worklogDate <= '{data_fim.date()}'"
            )
            
            logger.info(f"[JQL] Query: {jql}")
            
            # Buscar todas as issues com worklogs no período
            try:
                issues = await self._buscar_todas_issues_paginacao(
                    jql, 
                    fields=["key", "summary", "assignee", "worklog", "project", "created", "status", "customfield_10020", "parent", "issuetype"]
                )
                
                logger.info(f"[ISSUES] Encontradas {len(issues)} issues")
                
                # Log detalhado dos projetos encontrados
                projetos_encontrados = {}
                for issue in issues:
                    project_key = issue.get('key', '').split('-')[0] if issue.get('key') else 'UNKNOWN'
                    projetos_encontrados[project_key] = projetos_encontrados.get(project_key, 0) + 1
                
                logger.info(f"[PROJETOS_ENCONTRADOS] {projetos_encontrados}")
                
            except Exception as e:
                logger.error(f"[BUSCA_ISSUES_ERRO] Erro ao buscar issues: {str(e)}")
                raise
            
            for issue in issues:
                try:
                    issue_key = issue.get("key", "NO_KEY")
                    logger.info(f"[ISSUE_PROCESSANDO] Iniciando processamento de {issue_key}")
                    
                    await self._processar_issue(issue, data_inicio, data_fim)
                    self.stats['issues_processadas'] += 1
                    logger.info(f"[ISSUE_SUCESSO] Issue {issue_key} processada com sucesso")
                    
                except Exception as e:
                    issue_key = issue.get("key", "NO_KEY")
                    logger.error(f"[ISSUE_ERROR] Erro ao processar issue {issue_key}: {str(e)}")
                    logger.error(f"[ISSUE_ERROR] Traceback: ", exc_info=True)
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

    async def sincronizar_periodo(self, dias: int = 7) -> Dict[str, Any]:
        """Sincroniza últimos X dias (método de compatibilidade)"""
        data_inicio = datetime.now() - timedelta(days=dias)
        data_fim = datetime.now()
        
        try:
            await self.processar_periodo(data_inicio, data_fim)
            
            return {
                'status': 'SUCESSO',
                'message': f'Sincronização concluída: {self.stats["apontamentos_criados"]} apontamentos',
                **self.stats
            }
            
        except Exception as e:
            return {
                'status': 'ERRO',
                'message': str(e),
                **self.stats
            }

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
        projeto = await self.upsert_projeto(issue_key, issue_summary, secao.id, fields)
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
                await self._processar_worklog(worklog, issue_key, recurso.id, projeto.id, data_inicio, data_fim, fields)
            except Exception as e:
                wl_id = worklog.get("id", "NO_ID")
                logger.error(f"[WORKLOG_ERROR] Erro no worklog {wl_id}: {str(e)}")
                continue

    async def _processar_worklog(self, worklog: Dict[str, Any], issue_key: str, recurso_id: int, projeto_id: int, data_inicio: datetime, data_fim: datetime, fields: Dict[str, Any] = None):
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
        
        # Extrair campos de hierarquia Jira
        jira_parent_key = None
        jira_issue_type = None
        nome_subtarefa = None
        projeto_pai_id = None
        nome_projeto_pai = None
        
        if fields:
            # Detectar hierarquia (qualquer issue com parent)
            issuetype_data = fields.get("issuetype", {})
            jira_issue_type = issuetype_data.get("name")
            is_subtask = issuetype_data.get("subtask", False)
            parent_info = fields.get("parent")
            
            # Processar hierarquia se tiver parent (independente do tipo)
            if parent_info:
                jira_parent_key = parent_info.get("key")
                nome_subtarefa = fields.get("summary")
                
                logger.info(f"[HIERARQUIA] Issue {issue_key} tem parent {jira_parent_key} (tipo: {jira_issue_type})")
                
                # Buscar ou criar projeto pai se existir
                if jira_parent_key:
                    try:
                        projeto_pai = await self.projeto_repo.get_by_jira_project_key(jira_parent_key)
                        
                        if not projeto_pai:
                            # Projeto pai não existe, vamos buscar no Jira e criar
                            logger.info(f"[HIERARQUIA] Projeto pai {jira_parent_key} não existe, buscando no Jira...")
                            
                            try:
                                # Buscar issue pai no Jira
                                parent_issue = self.jira_client.get_issue(jira_parent_key)
                                if parent_issue:
                                    parent_fields = parent_issue.get('fields', {})
                                    parent_summary = parent_fields.get('summary', jira_parent_key)
                                    
                                    # Determinar seção do projeto pai
                                    parent_prefix = jira_parent_key.split("-")[0] if "-" in jira_parent_key else jira_parent_key
                                    parent_secao = await self.upsert_secao(parent_prefix)
                                    
                                    if parent_secao:
                                        # Criar projeto pai
                                        projeto_pai = await self.upsert_projeto(jira_parent_key, parent_summary, parent_secao.id, parent_fields)
                                        logger.info(f"[HIERARQUIA] Projeto pai {jira_parent_key} criado com ID {projeto_pai.id}")
                                    
                            except Exception as create_error:
                                logger.warning(f"[HIERARQUIA] Erro ao criar projeto pai {jira_parent_key}: {str(create_error)}")
                        
                        if projeto_pai:
                            projeto_pai_id = projeto_pai.id
                            nome_projeto_pai = projeto_pai.nome
                            logger.info(f"[HIERARQUIA] Projeto pai encontrado: {jira_parent_key} -> ID {projeto_pai_id}")
                            
                    except Exception as e:
                        logger.warning(f"[HIERARQUIA] Erro ao buscar/criar projeto pai {jira_parent_key}: {str(e)}")
        
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
            # Campos de hierarquia Jira
            "jira_parent_key": jira_parent_key,
            "jira_issue_type": jira_issue_type,
            "nome_subtarefa": nome_subtarefa,
            "projeto_pai_id": projeto_pai_id,
            "nome_projeto_pai": nome_projeto_pai,
        }
        
        # Criar/atualizar apontamento
        await self.apontamento_repo.sync_jira_apontamento(wl_id_str, apontamento_data)
        self.stats['apontamentos_criados'] += 1
        logger.debug(f"[APONTAMENTO] Criado para worklog {wl_id_str}: {horas}h")

    async def _buscar_todas_issues_paginacao(self, jql_query: str, fields: list = None):
        """Busca issues com paginação (copiado do melhorada.py)"""
        all_issues = []
        start_at = 0
        max_results = 100
        
        # Campos padrão se não especificados
        if not fields:
            fields = ["key", "summary", "assignee", "project", "parent", "issuetype", "timetracking", "timespent", "created", "status", "customfield_10020"]
        
        fields_str = ",".join(fields)
        
        while True:
            try:
                logger.info(f"[PAGINACAO] Buscando issues {start_at} a {start_at + max_results}")
                
                # Buscar com campos especificados
                response = self.jira_client._make_request(
                    "GET",
                    f"/rest/api/3/search?jql={jql_query}&startAt={start_at}&maxResults={max_results}&fields={fields_str}"
                )
                
                issues = response.get('issues', [])
                if not issues:
                    break
                
                all_issues.extend(issues)
                
                # Verificar se há mais páginas
                if len(issues) < max_results:
                    break
                    
                start_at += max_results
                
            except Exception as e:
                logger.error(f"[PAGINACAO_ERRO] {str(e)}")
                break
        
        return all_issues

    async def _processar_issue_completa_com_hierarquia(self, issue: Dict[str, Any]):
        """Processa issue completa COM HIERARQUIA (baseado no melhorada.py)"""
        issue_key = issue.get('key')
        fields = issue.get('fields', {})
        
        # Filtrar apenas projetos válidos das seções WEG
        project_key = issue_key.split('-')[0] if '-' in issue_key else None
        projetos_validos = ['SEG', 'SGI', 'DTIN', 'TIN']  # ✅ TODAS as seções WEG
        
        if not project_key or project_key not in projetos_validos:
            logger.debug(f"[ISSUE_SKIP] {issue_key} - Projeto {project_key} não é válido para sincronização")
            return {'apontamentos_processados': 0, 'recursos_criados': 0}
        
        logger.info(f"[ISSUE] Processando {issue_key}")
        
        # 1. EXTRAIR HIERARQUIA JIRA (baseado no JSON real)
        issuetype_data = fields.get("issuetype", {})
        jira_issue_type = issuetype_data.get("name")
        is_subtask = issuetype_data.get("subtask", False)
        parent_info = fields.get("parent")
        
        # 🔍 DEBUG: Log detalhado dos campos de hierarquia
        logger.info(f"[HIERARQUIA_DEBUG] {issue_key} - issuetype: {jira_issue_type}, subtask: {is_subtask}, parent_info: {parent_info}")
        
        jira_parent_key = None
        nome_subtarefa = None
        
        # Verificar se é subtask pelo campo subtask OU pela presença de parent
        if parent_info or is_subtask:
            if parent_info:
                jira_parent_key = parent_info.get("key")
            nome_subtarefa = fields.get("summary")
            logger.info(f"[HIERARQUIA] {issue_key} é subtarefa (parent: {jira_parent_key}, subtask: {is_subtask})")
        else:
            logger.info(f"[HIERARQUIA] {issue_key} é Epic/Task principal (tipo: {jira_issue_type}) - SEM PROJETO PAI")
        
        # 2. Obter/criar projeto e seção com dados completos do Jira
        project_data = fields.get('project', {})
        projeto = await self._obter_ou_criar_projeto(issue_key, project_data, fields)
        
        if not projeto:
            logger.error(f"[PROJETO_ERRO] {issue_key}")
            return {'apontamentos_processados': 0, 'recursos_criados': 0}
        
        # 3. Buscar/criar projeto pai (se for subtarefa)
        projeto_pai = None
        projeto_pai_id = None
        
        if jira_parent_key:
            parent_project_key = jira_parent_key.split('-')[0] if '-' in jira_parent_key else None
            
            # Filtrar apenas projetos pai válidos das seções WEG
            projetos_validos = ['SEG', 'SGI', 'DTIN', 'TIN']  # ✅ TODAS as seções WEG
            
            if parent_project_key and parent_project_key in projetos_validos:
                # Buscar projeto pai
                projeto_pai = await self.projeto_repository.get_by_jira_project_key(jira_parent_key)
                
                if not projeto_pai:
                    # Criar projeto pai baseado no Epic
                    try:
                        parent_issue_details = self.jira_client.get_issue(jira_parent_key)
                        parent_summary = parent_issue_details.get("fields", {}).get("summary", f"Epic {jira_parent_key}")
                        
                        status_projeto = await self.projeto_repository.get_status_default()
                        if status_projeto:
                            # Mapeamento correto: DTIN (Jira) → TIN (Seção)
                            secao_pai_key = parent_project_key
                            if parent_project_key == "DTIN":
                                secao_pai_key = "TIN"
                            
                            # Buscar seção do projeto pai
                            secao_pai = await self.secao_repository.get_by_jira_project_key(secao_pai_key)
                            
                            projeto_pai_data = {
                                "nome": parent_summary,
                                "jira_project_key": jira_parent_key,
                                "status_projeto_id": status_projeto.id,
                                "secao_id": secao_pai.id if secao_pai else None,
                                "ativo": True
                            }
                            
                            projeto_pai = await self.projeto_repository.create(projeto_pai_data)
                            self.stats['projetos_criados'] += 1
                            logger.info(f"[PROJETO_PAI_CRIADO] {projeto_pai.nome}")
                    
                    except Exception as e:
                        logger.error(f"[PROJETO_PAI_ERRO] {str(e)}")
                
                if projeto_pai:
                    projeto_pai_id = projeto_pai.id
        
        # 4. Usar timespent se disponível (corrigido baseado no JSON real)
        time_spent_seconds = fields.get('timespent', 0)
        if time_spent_seconds <= 0:
            # Fallback: tentar timetracking.timeSpentSeconds
            timetracking = fields.get('timetracking', {})
            time_spent_seconds = timetracking.get('timeSpentSeconds', 0)
        
        if time_spent_seconds > 0:
            # Usar assignee da issue para timetracking consolidado
            assignee = fields.get('assignee')
            if assignee:
                recurso = await self._obter_ou_criar_recurso(assignee)
                if recurso:
                    horas_totais = time_spent_seconds / 3600
                    await self._criar_apontamento_com_hierarquia(
                        issue_key, recurso, projeto, horas_totais, 
                        fields.get('summary', ''),
                        jira_parent_key, jira_issue_type, nome_subtarefa,
                        projeto_pai_id, projeto_pai, fields
                    )
                    return {'apontamentos_processados': 1, 'recursos_criados': 0}
        
        # 5. Fallback: processar worklogs individuais
        return await self._processar_worklogs_individuais_com_hierarquia(
            issue_key, projeto, 
            jira_parent_key, jira_issue_type, nome_subtarefa,
            projeto_pai_id, projeto_pai
        )

    async def _criar_apontamento_com_hierarquia(self, issue_key: str, recurso, projeto, 
                                               horas_totais: float, descricao: str,
                                               jira_parent_key: str, jira_issue_type: str, nome_subtarefa: str,
                                               projeto_pai_id: int, projeto_pai, fields: Dict[str, Any] = None):
        """Cria apontamento COM HIERARQUIA (baseado no melhorada.py)"""
        worklog_id_consolidado = f"consolidated_{issue_key}"
        
        # Verificar se já existe
        apontamento_existente = await self.apontamento_repository.get_by_jira_worklog_id(worklog_id_consolidado)
        
        # ✅ EXTRAIR DATA DE CRIAÇÃO REAL DO JIRA
        data_criacao = datetime.now()
        if fields:
            created_date = fields.get('created')
            if created_date:
                try:
                    data_criacao = parser.parse(created_date)
                    if data_criacao.tzinfo is not None:
                        data_criacao = data_criacao.replace(tzinfo=None)
                    logger.info(f"[APONTAMENTO] Data criação Jira: {data_criacao}")
                except Exception as e:
                    logger.warning(f"[APONTAMENTO] Erro ao parsear created: {e}")
        
        # DADOS COM HIERARQUIA COMPLETA
        apontamento_data = {
            'jira_worklog_id': worklog_id_consolidado,
            'recurso_id': recurso.id,
            'projeto_id': projeto.id,
            'jira_issue_key': issue_key,
            'jira_parent_key': jira_parent_key,                    # ✅ HIERARQUIA
            'jira_issue_type': jira_issue_type,                    # ✅ HIERARQUIA
            'nome_subtarefa': nome_subtarefa,                      # ✅ HIERARQUIA
            'projeto_pai_id': projeto_pai_id,                      # ✅ HIERARQUIA
            'nome_projeto_pai': projeto_pai.nome if projeto_pai else None,  # ✅ HIERARQUIA
            'data_apontamento': datetime.now().date(),
            'horas_apontadas': horas_totais,
            'descricao': descricao,
            'fonte_apontamento': FonteApontamento.JIRA,
            'data_sincronizacao_jira': datetime.now(),
            'data_atualizacao': datetime.now()
        }
        
        if apontamento_existente:
            # Atualizar
            for key, value in apontamento_data.items():
                setattr(apontamento_existente, key, value)
            await self.db.commit()
            logger.info(f"[APONTAMENTO] Consolidado atualizado: {issue_key} - {horas_totais}h")
        else:
            # Criar novo usando sync_jira_apontamento que faz commit
            apontamento_data['data_criacao'] = data_criacao
            worklog_id_consolidado = f"{issue_key}_consolidated_{int(datetime.now().timestamp())}"
            await self.apontamento_repository.sync_jira_apontamento(worklog_id_consolidado, apontamento_data)
            self.stats['apontamentos_criados'] += 1
            logger.info(f"[APONTAMENTO] Consolidado criado: {issue_key} - {horas_totais}h - Hierarquia: {jira_parent_key or 'Epic'}")

    async def _processar_worklogs_individuais_com_hierarquia(self, issue_key: str, projeto,
                                                            jira_parent_key: str, jira_issue_type: str, nome_subtarefa: str,
                                                            projeto_pai_id: int, projeto_pai):
        """Processa worklogs individuais COM HIERARQUIA"""
        try:
            worklogs = self.jira_client.get_all_worklogs(issue_key)
            logger.info(f"[WORKLOGS] {issue_key}: {len(worklogs)} worklogs")
            
            apontamentos_processados = 0
            
            for worklog in worklogs:
                try:
                    # Cada worklog tem seu próprio author
                    author = worklog.get('author', {})
                    if not author:
                        continue
                    
                    recurso = await self._obter_ou_criar_recurso(author)
                    if not recurso:
                        continue
                    
                    # Processar worklog individual
                    await self._processar_worklog_individual_com_hierarquia(
                        worklog, issue_key, recurso, projeto,
                        jira_parent_key, jira_issue_type, nome_subtarefa,
                        projeto_pai_id, projeto_pai
                    )
                    apontamentos_processados += 1
                    
                except Exception as e:
                    logger.error(f"[WORKLOG_ERRO] {worklog.get('id', 'N/A')}: {str(e)}")
                    continue
            
            return {'apontamentos_processados': apontamentos_processados, 'recursos_criados': 0}
            
        except Exception as e:
            logger.error(f"[WORKLOGS_ERRO] {issue_key}: {str(e)}")
            return {'apontamentos_processados': 0, 'recursos_criados': 0}

    async def _processar_worklog_individual_com_hierarquia(self, worklog: Dict[str, Any], issue_key: str, 
                                                          recurso, projeto,
                                                          jira_parent_key: str, jira_issue_type: str, nome_subtarefa: str,
                                                          projeto_pai_id: int, projeto_pai):
        """Processa worklog individual COM HIERARQUIA (baseado no melhorada.py)"""
        worklog_id = worklog.get('id')
        if not worklog_id:
            return
        
        # Verificar se já existe para UPSERT
        apontamento_existente = await self.apontamento_repository.get_by_jira_worklog_id(worklog_id)
        
        # Extrair dados do worklog
        time_spent_seconds = worklog.get('timeSpentSeconds', 0)
        if time_spent_seconds <= 0:
            return
        
        horas_apontadas = time_spent_seconds / 3600
        
        # Extrair data
        started = worklog.get('started')
        data_apontamento = datetime.now().date()
        if started:
            try:
                data_apontamento = parser.parse(started).date()
            except:
                pass
        
        # DADOS COM HIERARQUIA COMPLETA
        apontamento_data = {
            'jira_worklog_id': worklog_id,
            'recurso_id': recurso.id,
            'projeto_id': projeto.id,
            'jira_issue_key': issue_key,
            'jira_parent_key': jira_parent_key,                    # ✅ HIERARQUIA
            'jira_issue_type': jira_issue_type,                    # ✅ HIERARQUIA
            'nome_subtarefa': nome_subtarefa,                      # ✅ HIERARQUIA
            'projeto_pai_id': projeto_pai_id,                      # ✅ HIERARQUIA
            'nome_projeto_pai': projeto_pai.nome if projeto_pai else None,  # ✅ HIERARQUIA
            'data_apontamento': data_apontamento,
            'horas_apontadas': horas_apontadas,
            'descricao': extract_comment_text(worklog.get('comment')),
            'fonte_apontamento': FonteApontamento.JIRA,
            'data_sincronizacao_jira': datetime.now(),
            'data_atualizacao': datetime.now()
        }
        
        try:
            if apontamento_existente:
                # UPSERT: Atualizar apontamento existente
                logger.info(f"[WORKLOG_UPDATE] Atualizando apontamento existente: {worklog_id}")
                for key, value in apontamento_data.items():
                    setattr(apontamento_existente, key, value)
                await self.session.commit()
                logger.info(f"[WORKLOG_UPDATE_SUCESSO] Individual atualizado: {worklog_id} - {horas_apontadas}h - Hierarquia: {jira_parent_key or 'Epic'}")
            else:
                # UPSERT: Criar novo apontamento
                logger.info(f"[WORKLOG_CREATE] Criando novo apontamento: {worklog_id}")
                apontamento_data['data_criacao'] = datetime.now()
                await self.apontamento_repo.sync_jira_apontamento(worklog_id, apontamento_data)
                self.stats['apontamentos_criados'] += 1
                logger.info(f"[WORKLOG_CREATE_SUCESSO] Individual criado: {worklog_id} - {horas_apontadas}h - Hierarquia: {jira_parent_key or 'Epic'}")
                
        except Exception as e:
            logger.error(f"[WORKLOG_SAVE_ERROR] Erro ao salvar worklog {worklog_id}: {str(e)}")
            logger.error(f"[WORKLOG_SAVE_ERROR] Traceback: ", exc_info=True)
            await self.session.rollback()
            raise

    async def _obter_ou_criar_projeto(self, issue_key: str, project_data: Dict[str, Any], fields: Dict[str, Any] = None) -> Optional[Any]:
        """Obter/criar projeto e seção com dados completos do Jira"""
        try:
            # Buscar projeto existente pela issue_key
            projeto = await self.projeto_repository.get_by_jira_project_key(issue_key)
            if projeto:
                return projeto
            
            # Extrair dados do projeto Jira
            project_key = project_data.get('key', '')
            project_name = project_data.get('name', issue_key)
            
            # Mapeamento correto: DTIN (Jira) → TIN (Seção)
            secao_key = project_key
            if project_key == "DTIN":
                secao_key = "TIN"
            
            # Buscar seção pelo secao_key mapeado
            secao = await self.secao_repository.get_by_jira_project_key(secao_key)
            
            # Buscar status padrão
            status_projeto = await self.projeto_repository.get_status_default()
            if not status_projeto:
                logger.error(f"[PROJETO] Status padrão não encontrado")
                return None
            
            # ✅ EXTRAIR CAMPOS ADICIONAIS DO JIRA
            data_criacao = datetime.now()
            start_date = None
            jira_status = None
            
            if fields:
                # 1. Data de criação real do Jira
                created_date = fields.get('created')
                if created_date:
                    try:
                        data_criacao = parser.parse(created_date)
                        if data_criacao.tzinfo is not None:
                            data_criacao = data_criacao.replace(tzinfo=None)
                        logger.info(f"[PROJETO] Data criação Jira: {data_criacao}")
                    except Exception as e:
                        logger.warning(f"[PROJETO] Erro ao parsear created: {e}")
                
                # 2. Status do Jira
                status_data = fields.get('status', {})
                jira_status = status_data.get('name')
                if jira_status:
                    logger.info(f"[PROJETO] Status Jira: {jira_status}")
                
                # 3. StartDate do Sprint (customfield_10020)
                sprint_data = fields.get('customfield_10020', [])
                if sprint_data and len(sprint_data) > 0:
                    start_date_str = sprint_data[0].get('startDate')
                    if start_date_str:
                        try:
                            parsed_date = parser.parse(start_date_str)
                            if parsed_date.tzinfo is not None:
                                parsed_date = parsed_date.replace(tzinfo=None)
                            start_date = parsed_date.date()
                            logger.info(f"[PROJETO] Start date Sprint: {start_date}")
                        except Exception as e:
                            logger.warning(f"[PROJETO] Erro ao parsear startDate: {e}")
            
            # Criar projeto com dados completos
            projeto_data = {
                'nome': project_name,
                'jira_project_key': issue_key,
                'status_projeto_id': status_projeto.id,
                'secao_id': secao.id if secao else None,
                'ativo': True,
                'data_criacao': data_criacao,
                'data_inicio_prevista': start_date,  # ✅ CORRIGIDO: usar data_inicio_prevista
                'descricao': f"Status Jira: {jira_status}" if jira_status else None  # ✅ CORRIGIDO: usar descricao
            }
            
            projeto = await self.projeto_repository.create(projeto_data)
            self.stats['projetos_criados'] += 1
            logger.info(f"[PROJETO] Criado: {projeto.nome}")
            
            return projeto
            
        except Exception as e:
            logger.error(f"[PROJETO_ERRO] {issue_key}: {str(e)}")
            return None

    async def _obter_ou_criar_recurso(self, assignee_data: Dict[str, Any]):
        """Obter/criar recurso (copiado do melhorada.py)"""
        try:
            account_id = assignee_data.get('accountId')
            email = assignee_data.get('emailAddress')
            display_name = assignee_data.get('displayName')
            
            if not email:
                logger.warning(f"[RECURSO] Assignee sem email: {display_name}")
                return None
            
            # Buscar recurso existente
            recurso = await self.recurso_repository.get_by_jira_user_id(account_id)
            if not recurso:
                recurso = await self.recurso_repository.get_by_email(email)
            
            if recurso:
                return recurso
            
            # Criar novo recurso
            recurso_data = {
                'nome': display_name or email,
                'email': email,
                'jira_user_id': account_id,
                'ativo': True
            }
            
            recurso = await self.recurso_repository.create(recurso_data)
            self.stats['recursos_criados'] += 1
            logger.info(f"[RECURSO] Criado: {recurso.email}")
            
            return recurso
            
        except Exception as e:
            logger.error(f"[RECURSO_ERRO] {str(e)}")
            return None

# FUNÇÕES DE EXECUÇÃO BASEADAS NO CÓDIGO QUE FUNCIONAVA
async def processar_periodo(data_inicio: datetime, data_fim: datetime):
    """Função principal para processar um período"""
    async with AsyncSessionLocal() as session:
        sincronizador = SincronizacaoJiraFuncional(session)
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

async def sincronizar_dias(dias: int = 7):
    """Executa sincronização dos últimos X dias (compatibilidade)"""
    data_inicio = datetime.now() - timedelta(days=dias)
    data_fim = datetime.now()
    logger.info(f"[SYNC_DIAS] Sincronizando últimos {dias} dias")
    await processar_periodo(data_inicio, data_fim)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 3:
        # Período personalizado: python script.py 2024-08-01 2024-08-31
        asyncio.run(carga_personalizada(sys.argv[1], sys.argv[2]))
    elif len(sys.argv) == 2 and sys.argv[1] == "mensal":
        # Rotina mensal: python script.py mensal
        asyncio.run(rotina_mensal())
    elif len(sys.argv) == 2 and sys.argv[1].isdigit():
        # Últimos X dias: python script.py 7
        asyncio.run(sincronizar_dias(int(sys.argv[1])))
    else:
        # Carga completa: python script.py
        asyncio.run(carga_completa())
    
    print("✅ Sincronização concluída com sucesso!")
