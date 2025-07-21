"""
Serviço de sincronização melhorado do Jira.
Baseado na lógica que funcionou no Power BI e no mapeamento correto das entidades.
"""

import sys
import os

# Adicionar o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from dateutil import parser

from app.integrations.jira_client import JiraClient
from app.repositories.apontamento_repository import ApontamentoRepository
from app.repositories.recurso_repository import RecursoRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.secao_repository import SecaoRepository
from app.repositories.sincronizacao_jira_repository import SincronizacaoJiraRepository
from app.db.orm_models import FonteApontamento

logger = logging.getLogger(__name__)

class SincronizacaoJiraMelhorada:
    """
    Serviço de sincronização melhorado do Jira.
    
    MAPEAMENTO CORRETO:
    - Jira Project (ex: DTIN) → secao.jira_project_key
    - Jira Issue (ex: DTIN-7183) → projeto.jira_project_key  
    - Jira Assignee (accountId) → recurso.jira_user_id
    - Jira Worklog → apontamento.jira_worklog_id
    - timeSpentSeconds → apontamento.horas_apontadas
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.jira_client = JiraClient()
        self.apontamento_repository = ApontamentoRepository(db)
        self.recurso_repository = RecursoRepository(db)
        self.projeto_repository = ProjetoRepository(db)
        self.secao_repository = SecaoRepository(db)
        self.sincronizacao_repository = SincronizacaoJiraRepository(db)

    async def sincronizar_com_paginacao_robusta(self, dias: int = 7) -> Dict[str, Any]:
        """
        Sincroniza dados do Jira usando paginação robusta (baseada no Power BI que funciona).
        
        Args:
            dias: Número de dias para sincronizar
            
        Returns:
            Dict com resultado da sincronização
        """
        logger.info(f"[SYNC_MELHORADA] Iniciando sincronização de {dias} dias")
        
        try:
            # 1. Definir JQL para buscar issues com worklogs recentes
            data_inicio = datetime.now() - timedelta(days=dias)
            jql_query = f"worklogDate >= '{data_inicio.date()}'"
            
            # 2. Buscar todas as issues com paginação robusta (como no Power BI)
            issues = await self._buscar_todas_issues_paginacao(jql_query)
            logger.info(f"[SYNC_MELHORADA] Encontradas {len(issues)} issues")
            
            # 3. Processar cada issue
            contador_apontamentos = 0
            contador_recursos_criados = 0
            contador_erros = 0
            
            for issue in issues:
                try:
                    resultado = await self._processar_issue_completa(issue)
                    contador_apontamentos += resultado.get('apontamentos_processados', 0)
                    contador_recursos_criados += resultado.get('recursos_criados', 0)
                except Exception as e:
                    logger.error(f"[SYNC_MELHORADA] Erro ao processar issue {issue.get('key', 'N/A')}: {str(e)}")
                    contador_erros += 1
                    # Continua processando outras issues
            
            logger.info(f"[SYNC_MELHORADA] Sincronização concluída: {contador_apontamentos} apontamentos, {contador_recursos_criados} recursos criados, {contador_erros} erros")
            
            return {
                'status': 'SUCESSO',
                'apontamentos_processados': contador_apontamentos,
                'recursos_criados': contador_recursos_criados,
                'erros': contador_erros,
                'issues_processadas': len(issues)
            }
            
        except Exception as e:
            logger.error(f"[SYNC_MELHORADA] Erro geral na sincronização: {str(e)}")
            return {
                'status': 'ERRO',
                'mensagem': str(e)
            }

    async def _buscar_todas_issues_paginacao(self, jql_query: str) -> List[Dict[str, Any]]:
        """
        Busca todas as issues usando paginação robusta (baseada no Power BI que funciona).
        
        Args:
            jql_query: Query JQL para filtrar issues
            
        Returns:
            Lista de todas as issues encontradas
        """
        logger.info(f"[PAGINACAO] Iniciando busca com JQL: {jql_query}")
        
        # Campos essenciais (baseados no Power BI que funciona)
        fields = "key,summary,assignee,timetracking,timespent,project,worklog"
        
        all_issues = []
        start_at = 0
        max_results = 100
        
        while True:
            try:
                # Fazer requisição paginada
                endpoint = f"/rest/api/3/search"
                params = {
                    'jql': jql_query,
                    'startAt': start_at,
                    'maxResults': max_results,
                    'fields': fields
                }
                
                response = self.jira_client._make_request("GET", endpoint, params=params)
                
                issues = response.get('issues', [])
                total = response.get('total', 0)
                
                logger.info(f"[PAGINACAO] Página {start_at//max_results + 1}: {len(issues)} issues de {total}")
                
                all_issues.extend(issues)
                
                # Verificar se há mais páginas
                if len(all_issues) >= total or len(issues) == 0:
                    break
                    
                start_at += max_results
                
            except Exception as e:
                logger.error(f"[PAGINACAO] Erro na página {start_at//max_results + 1}: {str(e)}")
                break
        
        logger.info(f"[PAGINACAO] Total de issues obtidas: {len(all_issues)}")
        return all_issues

    async def _processar_issue_completa(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma issue completa, incluindo todos os worklogs.
        
        Args:
            issue: Dados da issue do Jira
            
        Returns:
            Dict com resultado do processamento
        """
        issue_key = issue.get('key', '')
        fields = issue.get('fields', {})
        
        logger.info(f"[PROCESSAR_ISSUE] Processando issue {issue_key}")
        
        # 1. Obter dados do assignee
        assignee = fields.get('assignee')
        if not assignee:
            logger.warning(f"[PROCESSAR_ISSUE] Issue {issue_key} sem assignee")
            return {'apontamentos_processados': 0, 'recursos_criados': 0}
        
        # 2. Obter/criar recurso
        recurso = await self._obter_ou_criar_recurso(assignee)
        if not recurso:
            logger.error(f"[PROCESSAR_ISSUE] Falha ao obter/criar recurso para {assignee.get('accountId')}")
            return {'apontamentos_processados': 0, 'recursos_criados': 0}
        
        # 3. Obter/criar projeto e seção
        projeto = await self._obter_ou_criar_projeto_secao(issue_key, fields.get('project', {}))
        if not projeto:
            logger.error(f"[PROCESSAR_ISSUE] Falha ao obter/criar projeto para {issue_key}")
            return {'apontamentos_processados': 0, 'recursos_criados': 0}
        
        # 4. Processar worklogs da issue
        worklog_data = fields.get('worklog', {})
        worklogs = worklog_data.get('worklogs', [])
        
        # 5. Usar timetracking.timeSpentSeconds se disponível (lógica do Power BI)
        timetracking = fields.get('timetracking', {})
        time_spent_seconds = timetracking.get('timeSpentSeconds', 0)
        
        if time_spent_seconds and time_spent_seconds > 0:
            # Usar timetracking.timeSpentSeconds (soma correta de TODOS os worklogs)
            horas_totais = time_spent_seconds / 3600
            
            # Criar/atualizar apontamento consolidado
            await self._criar_apontamento_consolidado(
                issue_key=issue_key,
                recurso=recurso,
                projeto=projeto,
                horas_totais=horas_totais,
                descricao=fields.get('summary', '')
            )
            
            return {'apontamentos_processados': 1, 'recursos_criados': 0}
        
        # 6. Fallback: processar worklogs individuais
        apontamentos_processados = 0
        for worklog in worklogs:
            try:
                await self._processar_worklog_individual(worklog, issue_key, recurso, projeto)
                apontamentos_processados += 1
            except Exception as e:
                logger.error(f"[PROCESSAR_ISSUE] Erro ao processar worklog {worklog.get('id')}: {str(e)}")
        
        return {'apontamentos_processados': apontamentos_processados, 'recursos_criados': 0}

    async def _obter_ou_criar_recurso(self, assignee_data: Dict[str, Any]) -> Optional[Any]:
        """
        Obtém um recurso existente ou cria um novo automaticamente.
        
        Args:
            assignee_data: Dados do assignee do Jira
            
        Returns:
            Recurso encontrado ou criado
        """
        account_id = assignee_data.get('accountId')
        if not account_id:
            return None
        
        # 1. Tentar encontrar recurso existente
        recurso = await self.recurso_repository.get_by_jira_user_id(account_id)
        
        if recurso:
            logger.info(f"[RECURSO] Recurso encontrado: {recurso.nome} ({account_id})")
            
            # 2. Atualizar dados do recurso se necessário
            nome_atual = assignee_data.get('displayName', '')
            email_atual = assignee_data.get('emailAddress', '')
            
            if nome_atual and nome_atual != recurso.nome:
                recurso.nome = nome_atual
                await self.db.commit()
                logger.info(f"[RECURSO] Nome atualizado para: {nome_atual}")
            
            return recurso
        
        # 3. Criar novo recurso automaticamente
        logger.info(f"[RECURSO] Criando novo recurso para {account_id}")
        
        novo_recurso_data = {
            'nome': assignee_data.get('displayName', f'Usuário {account_id}'),
            'email': assignee_data.get('emailAddress', f'{account_id}@weg.net'),
            'jira_user_id': account_id,
            'ativo': True,
            'data_criacao': datetime.now(),
            'data_atualizacao': datetime.now()
        }
        
        try:
            novo_recurso = await self.recurso_repository.create(novo_recurso_data)
            logger.info(f"[RECURSO] Recurso criado: {novo_recurso.nome} (ID: {novo_recurso.id})")
            return novo_recurso
        except Exception as e:
            logger.error(f"[RECURSO] Erro ao criar recurso: {str(e)}")
            return None

    async def _obter_ou_criar_projeto_secao(self, issue_key: str, project_data: Dict[str, Any]) -> Optional[Any]:
        """
        Obtém um projeto existente ou cria seção/projeto automaticamente.
        
        Args:
            issue_key: Chave da issue (ex: DTIN-7183)
            project_data: Dados do projeto do Jira
            
        Returns:
            Projeto encontrado ou criado
        """
        # 1. Extrair chave do projeto da issue (ex: DTIN-7183 → DTIN)
        projeto_key = issue_key.split('-')[0] if '-' in issue_key else None
        if not projeto_key:
            return None
        
        # 2. Buscar projeto existente
        projeto = await self.projeto_repository.get_by_jira_project_key(projeto_key)
        if projeto:
            logger.info(f"[PROJETO] Projeto encontrado: {projeto.nome} ({projeto_key})")
            return projeto
        
        # 3. Buscar/criar seção primeiro
        secao = await self.secao_repository.get_by_jira_project_key(projeto_key)
        if not secao:
            # Criar seção automaticamente
            nova_secao_data = {
                'nome': project_data.get('name', f'Seção {projeto_key}'),
                'jira_project_key': projeto_key,
                'ativo': True,
                'data_criacao': datetime.now(),
                'data_atualizacao': datetime.now()
            }
            
            try:
                secao = await self.secao_repository.create(nova_secao_data)
                logger.info(f"[SECAO] Seção criada: {secao.nome} ({projeto_key})")
            except Exception as e:
                logger.error(f"[SECAO] Erro ao criar seção: {str(e)}")
                return None
        
        # 4. Criar projeto automaticamente
        novo_projeto_data = {
            'nome': f'Projeto {issue_key}',
            'jira_project_key': projeto_key,
            'secao_id': secao.id,
            'status_projeto_id': 1,  # Status padrão
            'ativo': True,
            'data_criacao': datetime.now(),
            'data_atualizacao': datetime.now()
        }
        
        try:
            projeto = await self.projeto_repository.create(novo_projeto_data)
            logger.info(f"[PROJETO] Projeto criado: {projeto.nome} (ID: {projeto.id})")
            return projeto
        except Exception as e:
            logger.error(f"[PROJETO] Erro ao criar projeto: {str(e)}")
            return None

    async def _criar_apontamento_consolidado(self, issue_key: str, recurso: Any, projeto: Any, 
                                           horas_totais: float, descricao: str) -> None:
        """
        Cria ou atualiza um apontamento consolidado usando timetracking.timeSpentSeconds.
        
        Args:
            issue_key: Chave da issue
            recurso: Recurso responsável
            projeto: Projeto relacionado
            horas_totais: Total de horas (de timetracking.timeSpentSeconds)
            descricao: Descrição do apontamento
        """
        # Usar issue_key como identificador único para apontamento consolidado
        worklog_id_consolidado = f"consolidated_{issue_key}"
        
        # Verificar se já existe apontamento consolidado
        apontamento_existente = await self.apontamento_repository.get_by_jira_worklog_id(worklog_id_consolidado)
        
        apontamento_data = {
            'jira_worklog_id': worklog_id_consolidado,
            'recurso_id': recurso.id,
            'projeto_id': projeto.id,
            'jira_issue_key': issue_key,
            'data_apontamento': datetime.now().date(),
            'horas_apontadas': horas_totais,
            'descricao': descricao,
            'fonte_apontamento': FonteApontamento.JIRA,
            'data_sincronizacao_jira': datetime.now(),
            'data_atualizacao': datetime.now()
        }
        
        if apontamento_existente:
            # Atualizar apontamento existente
            for key, value in apontamento_data.items():
                setattr(apontamento_existente, key, value)
            await self.db.commit()
            logger.info(f"[APONTAMENTO] Apontamento consolidado atualizado: {issue_key} - {horas_totais}h")
        else:
            # Criar novo apontamento
            apontamento_data['data_criacao'] = datetime.now()
            await self.apontamento_repository.create(apontamento_data)
            logger.info(f"[APONTAMENTO] Apontamento consolidado criado: {issue_key} - {horas_totais}h")

    async def _processar_worklog_individual(self, worklog: Dict[str, Any], issue_key: str, 
                                          recurso: Any, projeto: Any) -> None:
        """
        Processa um worklog individual (fallback quando timetracking não disponível).
        
        Args:
            worklog: Dados do worklog
            issue_key: Chave da issue
            recurso: Recurso responsável
            projeto: Projeto relacionado
        """
        worklog_id = worklog.get('id')
        if not worklog_id:
            return
        
        # Verificar se já existe
        apontamento_existente = await self.apontamento_repository.get_by_jira_worklog_id(worklog_id)
        if apontamento_existente:
            logger.info(f"[WORKLOG] Worklog {worklog_id} já existe")
            return
        
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
        
        # Criar apontamento
        apontamento_data = {
            'jira_worklog_id': worklog_id,
            'recurso_id': recurso.id,
            'projeto_id': projeto.id,
            'jira_issue_key': issue_key,
            'data_apontamento': data_apontamento,
            'horas_apontadas': horas_apontadas,
            'descricao': worklog.get('comment', {}).get('content', [{}])[0].get('content', [{}])[0].get('text', '') if worklog.get('comment') else '',
            'fonte_apontamento': FonteApontamento.JIRA,
            'data_sincronizacao_jira': datetime.now(),
            'data_criacao': datetime.now(),
            'data_atualizacao': datetime.now()
        }
        
        await self.apontamento_repository.create(apontamento_data)
        logger.info(f"[WORKLOG] Worklog individual criado: {worklog_id} - {horas_apontadas}h")
