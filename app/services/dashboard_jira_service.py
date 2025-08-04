"""
Serviço de Dashboard JIRA - Indicadores do Departamento
Baseado nos JQLs fornecidos para criar dashboards filtráveis por data, seção e recurso.

Dashboards suportados:
1. Demandas (Portfólio) - Epics com label TIN-Projetos
2. Melhorias - Epics com label TIN-Melhorias  
3. Recursos Alocados (Atividades) - Issues por assignee em outras áreas

Filtros disponíveis:
- Data: updated >= X AND updated <= Y
- Seção: Projetos Jira (DTIN, SEG, SGI)
- Recurso: assignee in (lista_de_ids)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from app.integrations.jira_client import JiraClient

logger = logging.getLogger(__name__)

@dataclass
class DashboardFilters:
    """Filtros para os dashboards"""
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    secao: Optional[str] = None  # DTIN, SEG, SGI
    recursos: Optional[List[str]] = None  # Lista de jira_user_ids
    ano: Optional[int] = None

@dataclass
class DashboardItem:
    """Item do dashboard com contadores por status"""
    status: str
    quantidade: int
    percentual: float

@dataclass
class DashboardResponse:
    """Resposta do dashboard"""
    tipo: str  # demandas, melhorias, recursos_alocados
    total: int
    items: List[DashboardItem]
    filtros_aplicados: Dict[str, Any]

class DashboardJiraService:
    """Serviço para dashboards baseados em dados do Jira"""
    
    def __init__(self):
        self.jira_client = JiraClient()
        
        # Mapeamento de status do Jira para cores/grupos
        self.status_mapping = {
            "IN PROGRESS": {"nome": "In Progress", "cor": "#1f77b4"},
            "To Do": {"nome": "To Do", "cor": "#17becf"},
            "On Hold": {"nome": "Standby/On Hold", "cor": "#bcbd22"},
            "Done": {"nome": "Done", "cor": "#2ca02c"},
            "Standby": {"nome": "Standby/On Hold", "cor": "#bcbd22"},
            "Cancelled": {"nome": "Cancelled", "cor": "#d62728"}
        }
    
    def _build_base_jql(self, filters: DashboardFilters) -> str:
        """Constrói JQL base com filtros comuns"""
        jql_parts = []
        
        # Filtro de seção (projeto)
        if filters.secao:
            if filters.secao == "DTIN":
                jql_parts.append('(project = DTIN OR project = "Technology Business Management - TI")')
            elif filters.secao == "SEG":
                jql_parts.append('(project = "SEG Seção Segurança da Informação e Riscos TI" OR project = "Gerenciamento Vulnerabilidades ")')
            elif filters.secao == "SGI":
                jql_parts.append('project = "SGI - Seção Suporte Global Infraestrutura"')
        
        # Filtro de data (updated)
        if filters.data_inicio:
            jql_parts.append(f'updated >= "{filters.data_inicio.strftime("%Y-%m-%d")}"')
        
        if filters.data_fim:
            jql_parts.append(f'updated <= "{filters.data_fim.strftime("%Y-%m-%d")} 23:59"')
        
        # Filtro de ano padrão se não especificado
        if not filters.data_inicio and not filters.data_fim:
            ano = filters.ano or datetime.now().year
            jql_parts.append(f'updated >= "{ano}-01-01"')
            jql_parts.append(f'updated <= "{ano}-12-31 23:59"')
        
        # Status padrão para todos os dashboards
        status_filter = '(status = "IN PROGRESS" OR status = "To Do" OR status = "On Hold" OR status = Done OR status = Standby OR status = Cancelled)'
        jql_parts.append(status_filter)
        
        return " AND ".join(jql_parts)
    
    def _build_demandas_jql(self, filters: DashboardFilters) -> str:
        """Constrói JQL para Demandas (Portfólio)"""
        jql_parts = []
        
        if filters.secao == "DTIN":
            # JQL para DTIN - Demandas (Portfólio) - EXATO conforme fornecido
            jql_parts = [
                "project = DTIN",
                "issuetype = Epic",
                "labels = TIN-Projetos"
            ]
        elif filters.secao == "SEG":
            jql_parts.extend([
                '(project = "SEG Seção Segurança da Informação e Riscos TI" OR project = "Gerenciamento Vulnerabilidades ")',
                'issuetype = Epic',
                'labels = SEG-Projetos',
                'key != SEG-3073'
            ])
        elif filters.secao == "SGI":
            # JQL para SGI - Demandas (Portfólio) - EXATO conforme fornecido
            jql_parts = [
                'project = "SGI - Seção Suporte Global Infraestrutura"',
                'issuetype = Epic',
                'labels = SGI-Projetos'
            ]
        else:
            # Busca todas as seções
            jql_parts.extend([
                'issuetype = Epic',
                '(labels = TIN-Projetos OR labels = SEG-Projetos OR labels = SGI-Projetos)'
            ])
        
        # Status padrão
        jql_parts.append('(status = "IN PROGRESS" OR status = "To Do" OR status = "On Hold" OR status = Done OR status = Standby OR status = Cancelled)')
        
        # Filtros de data - DTIN usa 09/01 como início
        ano = filters.ano or 2025
        if filters.data_inicio and filters.data_fim:
            # Normalizar datas para formato aceito pelo Jira (YYYY-MM-DD)
            # Tratar tanto strings quanto objetos datetime
            if isinstance(filters.data_inicio, str):
                data_inicio = filters.data_inicio.split('T')[0] if 'T' in filters.data_inicio else filters.data_inicio
            else:
                data_inicio = filters.data_inicio.strftime('%Y-%m-%d')
            
            if isinstance(filters.data_fim, str):
                data_fim = filters.data_fim.split('T')[0] if 'T' in filters.data_fim else filters.data_fim
            else:
                data_fim = filters.data_fim.strftime('%Y-%m-%d')
            jql_parts.append(f'updated >= "{data_inicio}" AND updated <= "{data_fim}"')
        else:
            # Data específica por seção conforme JQLs fornecidos
            if filters.secao == "DTIN":
                jql_parts.append(f'updated >= {ano}-01-09 AND updated <= "{ano}-12-31 23:59"')
                jql_parts.append('created >= 2023-01-01')
            elif filters.secao == "SGI":
                jql_parts.append(f'updated >= {ano}-01-01 AND updated <= "{ano}-12-31 23:59"')
            elif filters.secao == "SEG":
                jql_parts.append(f'updated >= {ano}-01-01 AND updated <= {ano}-12-31')
            else:
                jql_parts.append(f'updated >= {ano}-01-01 AND updated <= {ano}-12-31')
        
        return ' AND '.join(jql_parts)
    
    def _build_melhorias_jql(self, filters: DashboardFilters) -> str:
        """Constrói JQL para Melhorias"""
        jql_parts = []
        
        # Filtros específicos por seção
        if filters.secao == "DTIN":
            jql_parts.extend([
                '(project = DTIN OR project = "Technology Business Management - TI")',
                'issuetype = Epic',
                'labels = TIN-Melhorias'
            ])
        elif filters.secao == "SEG":
            jql_parts.extend([
                '(project = "SEG Seção Segurança da Informação e Riscos TI" OR project = "Gerenciamento Vulnerabilidades ")',
                'issuetype = Epic',
                '(labels = SEG-Melhorias OR labels = SEG-Rotinas OR labels = SEG-Consultorias)',
                'component != "Data Management and Solution and Analytics"'
            ])
        elif filters.secao == "SGI":
            jql_parts.extend([
                'project = "SGI - Seção Suporte Global Infraestrutura"',
                'issuetype = Epic',
                'labels = SGI-Melhorias'
            ])
        else:
            # Busca todas as seções
            jql_parts.extend([
                'issuetype = Epic',
                '(labels = TIN-Melhorias OR labels = SEG-Melhorias OR labels = SEG-Rotinas OR labels = SEG-Consultorias OR labels = SGI-Melhorias)'
            ])
        
        # Status padrão
        jql_parts.append('(status = "IN PROGRESS" OR status = "To Do" OR status = "On Hold" OR status = Done OR status = Standby OR status = Cancelled)')
        
        # Filtros de data
        ano = filters.ano or 2025
        if filters.data_inicio and filters.data_fim:
            # Normalizar datas para formato aceito pelo Jira (YYYY-MM-DD)
            # Tratar tanto strings quanto objetos datetime
            if isinstance(filters.data_inicio, str):
                data_inicio = filters.data_inicio.split('T')[0] if 'T' in filters.data_inicio else filters.data_inicio
            else:
                data_inicio = filters.data_inicio.strftime('%Y-%m-%d')
            
            if isinstance(filters.data_fim, str):
                data_fim = filters.data_fim.split('T')[0] if 'T' in filters.data_fim else filters.data_fim
            else:
                data_fim = filters.data_fim.strftime('%Y-%m-%d')
            jql_parts.append(f'updated >= "{data_inicio}" AND updated <= "{data_fim}"')
        else:
            jql_parts.append(f'updated >= {ano}-01-01 AND updated <= {ano}-12-31')
        
        return ' AND '.join(jql_parts)
    
    def _build_recursos_alocados_jql(self, filters: DashboardFilters) -> str:
        """Constrói JQL para Recursos Alocados (Atividades)"""
        jql_parts = []
        
        # Filtros específicos por seção conforme JQLs fornecidos
        if filters.secao == "DTIN":
            # Assignees específicos para DTIN conforme JQL fornecido
            assignees_dtin = [
                "712020:25cb4a8b-979a-4a2b-9106-b66c201c6b38",
                "62bb912ffa171a27239d302b",
                "5dc1db5f16a90b0df7c6e8dd",
                "70121:113b7da8-4f79-4f7e-b8f3-34f23cc48502",
                "712020:1ee5db5e-1159-43b8-bb36-4a3e0c8d1c3b",
                "712020:57804f76-1bef-4121-9570-0a1a5183a546",
                "712020:17c89c8a-5040-470a-9db9-26804fa33df8",
                "5d0952ac5977d60c29e1b498",
                "5f732988a290960075eb5589",
                "557058:bca80583-58de-4da5-9b7f-93dcc8f9dd27",
                "70121:afff999b-3808-4448-82cb-9f6c90d0aaff",
                "5f610105cacd830077629277",
                "712020:6905028a-6a78-4bef-acbd-fb678e4628dd",
                "62fe33231e82e839c250729c",
                "62e190ea3780798663d0a667",
                "712020:dad51d6e-21ac-4100-b87f-545328dad4ac",
                "712020:3b76bf36-4628-4202-ac42-f8346a2f8325",
                "712020:a8514790-f98f-4f6f-b304-72a8c9c7dba2",
                "712020:27aba0ba-1c77-4efd-b6ae-673c5d945737",
                "712020:026dd53c-bc8d-4cc2-9dc9-792b36ddf8b2",
                "557058:93437de9-7cb5-490c-928a-326f6becdfaa"
            ]
            
            # Filtro de recursos customizado sobrescreve assignees padrão
            if filters.recursos and len(filters.recursos) > 0:
                assignees_str = ", ".join(filters.recursos)
                jql_parts.append(f"assignee in ({assignees_str})")
            else:
                # Usar assignees padrão da DTIN
                assignees_str = ", ".join(assignees_dtin)
                jql_parts.append(f"assignee in ({assignees_str})")
            
            jql_parts.extend([
                'issuetype != Epic',
                'project != "TIN Seção Tecnologia de Infraestrutura"',
                'project != "Technology Business Management - TI"',
                'project != "Atividades PMO TIN"',
                'created >= 2023-08-01'
            ])
        elif filters.secao == "SEG":
            # Assignees específicos para SEG conforme JQL fornecido
            assignees_seg = [
                "712020:9af484a8-e9f7-4f30-85cf-7c6346dc9602",
                "5f99c99a7cfc24007196835a",
                "712020:9f2f3e0b-7a12-4951-b312-b00fca2ac792",
                "712020:060778c7-d62a-41b9-898e-582c7d007011",
                "712020:7d772268-a4d1-48ff-aa38-a6094a4c85b8",
                "712020:aad81c3d-eb9b-439b-89f1-7144ba810218",
                "712020:5c9028a1-32be-458e-afa5-10d4c32f425f",
                "712020:83439bb3-e5ec-4650-8e31-a88815b6492a",
                "712020:1ec85bfe-accf-4781-9989-106d9418e67c",
                "712020:3337a5b2-ce3a-4b3a-83ed-a2748daca478",
                "712020:a43ab850-0d40-4c1b-9fc7-b109ce5def90",
                "712020:52671dd9-6858-49a1-aa8d-b719ba996d64",
                "712020:6dfa0ef9-a74f-4d67-a3ed-29902b888632"
            ]
            
            # Filtro de recursos customizado sobrescreve assignees padrão
            if filters.recursos and len(filters.recursos) > 0:
                assignees_str = ", ".join(filters.recursos)
                jql_parts.append(f"assignee in ({assignees_str})")
            else:
                # Usar assignees padrão da SEG
                assignees_str = ", ".join(assignees_seg)
                jql_parts.append(f"assignee in ({assignees_str})")
            
            jql_parts.extend([
                'issuetype != Epic',
                'project != "SEG Seção Segurança da Informação e Riscos TI"',
                'project != "Atividades PMO TIN"',
                'project != "Gerenciamento Vulnerabilidades "',
                'key != DLT-572'
            ])
        elif filters.secao == "SGI":
            # Assignees específicos para SGI conforme JQL fornecido
            assignees_sgi = [
                "70121:5a07e1ec-a96e-44a6-916a-179c55379da1",
                "712020:91f2b81c-c68e-41b8-9c51-11d2980eb612",
                "712020:b7068ff3-8a5a-499a-bca5-d05bc5444a03",
                "712020:c01a5c64-749b-4f28-bd74-74e9a47ba059",
                "712020:55f40d9f-7086-4345-9135-86abb88b995c",
                "712020:fffaf56b-85dd-49cc-a3d3-028c927f12c6",
                "712020:cf6445bb-57e5-4361-b9be-cc321fba9bb2",
                "62bb913c37780d89a3513a9b",
                "712020:ef316294-89a1-4563-a18b-3521a383b1e5",
                "712020:73daa4b9-c93b-4f20-b1b5-94fe9fc5b112",
                "712020:e42068cb-446e-4775-8eb4-3361a418ddcd",
                "712020:8e485520-fbfd-4e06-80b2-1aef3d72f248"
            ]
            
            # Filtro de recursos customizado sobrescreve assignees padrão
            if filters.recursos and len(filters.recursos) > 0:
                assignees_str = ", ".join(filters.recursos)
                jql_parts.append(f"assignee in ({assignees_str})")
            else:
                # Usar assignees padrão da SGI
                assignees_str = ", ".join(assignees_sgi)
                jql_parts.append(f"assignee in ({assignees_str})")
            
            jql_parts.extend([
                'issuetype != Epic',
                'project != "SGI - Seção Suporte Global Infraestrutura"',
                'project != "PlatformOPS & CCoE"',
                'created >= 2024-01-01'
            ])
        
        # Lógica para seções sem assignees hardcoded
        else:
            # Base comum para recursos alocados
            jql_parts.append('issuetype != Epic')
            
            # Filtro de recursos customizado (se fornecido)
            if filters.recursos and len(filters.recursos) > 0:
                assignees_str = ", ".join(filters.recursos)
                jql_parts.append(f"assignee in ({assignees_str})")
        
        # Status padrão
        jql_parts.append('(status = "IN PROGRESS" OR status = "To Do" OR status = "On Hold" OR status = Done OR status = Standby)')
        
        # Filtros de data
        ano = filters.ano or 2025
        if filters.data_inicio and filters.data_fim:
            # Normalizar datas para formato aceito pelo Jira (YYYY-MM-DD)
            # Tratar tanto strings quanto objetos datetime
            if isinstance(filters.data_inicio, str):
                data_inicio = filters.data_inicio.split('T')[0] if 'T' in filters.data_inicio else filters.data_inicio
            else:
                data_inicio = filters.data_inicio.strftime('%Y-%m-%d')
            
            if isinstance(filters.data_fim, str):
                data_fim = filters.data_fim.split('T')[0] if 'T' in filters.data_fim else filters.data_fim
            else:
                data_fim = filters.data_fim.strftime('%Y-%m-%d')
            jql_parts.append(f'updated >= "{data_inicio}" AND updated <= "{data_fim}"')
        else:
            jql_parts.append(f'updated >= {ano}-01-01 AND updated <= {ano}-12-31')
        
        # Filtro adicional de criação para SEG - já incluído nos filtros de data acima
        
        # Filtros específicos por seção
        if filters.secao == "DTIN":
            jql_parts.append('"SAP PPM" != "2023_09 | DTI_Atividades de Rotina | Atividades de Rotina | 00000000000000080022 | 000006017280"')
        
        # ORDER BY específico por seção
        if filters.secao == "SGI":
            return ' AND '.join(jql_parts) + ' ORDER BY status DESC, priority DESC'
        else:
            return ' AND '.join(jql_parts) + ' ORDER BY status ASC'
    
    async def get_demandas_dashboard(self, filters: DashboardFilters) -> DashboardResponse:
        """Obtém dados do dashboard de Demandas (Portfólio)"""
        try:
            logger.info(f"[DEMANDAS_DASHBOARD] Iniciando consulta com filtros: {filters}")
            
            jql = self._build_demandas_jql(filters)
            logger.info(f"[DEMANDAS_JQL] {jql}")
            
            # Buscar issues do Jira
            issues = await self._buscar_issues_paginacao(jql)
            
            # Processar contadores por status
            status_counts = {}
            total = len(issues)
            
            for issue in issues:
                status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Converter para formato de resposta
            items = []
            for status, count in status_counts.items():
                percentual = (count / total * 100) if total > 0 else 0
                items.append(DashboardItem(
                    status=status,
                    quantidade=count,
                    percentual=round(percentual, 1)
                ))
            
            logger.info(f"[DEMANDAS_RESULT] Total: {total}, Status: {status_counts}")
            
            return DashboardResponse(
                tipo="demandas",
                total=total,
                items=items,
                filtros_aplicados=filters.__dict__
            )
            
        except Exception as e:
            logger.error(f"[DEMANDAS_ERROR] Erro ao buscar demandas: {str(e)}")
            raise
    
    async def get_melhorias_dashboard(self, filters: DashboardFilters) -> DashboardResponse:
        """Obtém dados do dashboard de Melhorias"""
        try:
            logger.info(f"[MELHORIAS_DASHBOARD] Iniciando consulta com filtros: {filters}")
            
            jql = self._build_melhorias_jql(filters)
            logger.info(f"[MELHORIAS_JQL] {jql}")
            
            # Buscar issues do Jira
            issues = await self._buscar_issues_paginacao(jql)
            
            # Processar contadores por status
            status_counts = {}
            total = len(issues)
            
            for issue in issues:
                status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Converter para formato de resposta
            items = []
            for status, count in status_counts.items():
                percentual = (count / total * 100) if total > 0 else 0
                items.append(DashboardItem(
                    status=status,
                    quantidade=count,
                    percentual=round(percentual, 1)
                ))
            
            logger.info(f"[MELHORIAS_RESULT] Total: {total}, Status: {status_counts}")
            
            return DashboardResponse(
                tipo="melhorias",
                total=total,
                items=items,
                filtros_aplicados=filters.__dict__
            )
            
        except Exception as e:
            logger.error(f"[MELHORIAS_ERROR] Erro ao buscar melhorias: {str(e)}")
            raise
    
    async def get_recursos_alocados_dashboard(self, filters: DashboardFilters) -> DashboardResponse:
        """Obtém dados do dashboard de Recursos Alocados (Atividades)"""
        try:
            logger.info(f"[RECURSOS_DASHBOARD] Iniciando consulta com filtros: {filters}")
            
            jql = self._build_recursos_alocados_jql(filters)
            logger.info(f"[RECURSOS_JQL] {jql}")
            
            # Buscar issues do Jira com limite menor para recursos alocados (evita travamento)
            issues = await self._buscar_issues_paginacao(jql, max_issues=2000)
            
            # Processar contadores por status
            status_counts = {}
            total = len(issues)
            
            for issue in issues:
                status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Converter para formato de resposta
            items = []
            for status, count in status_counts.items():
                percentual = (count / total * 100) if total > 0 else 0
                items.append(DashboardItem(
                    status=status,
                    quantidade=count,
                    percentual=round(percentual, 1)
                ))
            
            logger.info(f"[RECURSOS_RESULT] Total: {total}, Status: {status_counts}")
            
            return DashboardResponse(
                tipo="recursos_alocados",
                total=total,
                items=items,
                filtros_aplicados=filters.__dict__
            )
            
        except Exception as e:
            logger.error(f"[RECURSOS_ERROR] Erro ao buscar recursos alocados: {str(e)}")
            raise
    
    async def _buscar_issues_paginacao(self, jql_query: str, fields: List[str] = None, max_issues: int = 5000) -> List[Dict[str, Any]]:
        """Busca issues com paginação e limite para evitar travamentos"""
        if fields is None:
            fields = ["key", "summary", "status", "assignee", "created", "updated"]
        
        try:
            logger.info(f"[PAGINACAO] Iniciando busca com JQL: {jql_query} (limite: {max_issues} issues)")
            
            # Buscar apenas uma amostra para dashboards (não todas as issues)
            issues = []
            start_at = 0
            page_size = 100
            
            while len(issues) < max_issues:
                # Calcular quantas issues buscar nesta página
                remaining = max_issues - len(issues)
                current_page_size = min(page_size, remaining)
                
                logger.info(f"[PAGINACAO_PAGE] Buscando página {start_at//page_size + 1}, issues {start_at}-{start_at + current_page_size}")
                
                # Buscar página atual usando método correto do JiraClient
                page_response = self.jira_client._make_request("POST", "/rest/api/3/search", {
                    "jql": jql_query,
                    "fields": fields,
                    "startAt": start_at,
                    "maxResults": current_page_size
                })
                
                if not page_response or len(page_response.get('issues', [])) == 0:
                    logger.info(f"[PAGINACAO_END] Não há mais issues para buscar")
                    break
                
                issues.extend(page_response['issues'])
                
                # Se retornou menos que o solicitado, chegou ao fim
                if len(page_response['issues']) < current_page_size:
                    logger.info(f"[PAGINACAO_END] Última página encontrada")
                    break
                
                start_at += current_page_size
            
            logger.info(f"[PAGINACAO_FINAL] Total de issues carregadas: {len(issues)} (limite: {max_issues})")
            return issues
                
        except Exception as e:
            logger.error(f"[PAGINACAO_ERROR] Erro na paginação: {str(e)}")
            raise
    
    async def get_recursos_disponiveis(self, secao: str = None) -> List[Dict[str, str]]:
        """Obtém lista de recursos (assignees) disponíveis para filtros"""
        try:
            # JQL para buscar assignees únicos da seção
            jql_base = "assignee is not EMPTY"
            
            if secao:
                if secao == "DTIN":
                    jql_base += ' AND (project = DTIN OR project = "Technology Business Management - TI")'
                elif secao == "SEG":
                    jql_base += ' AND project = SEG'
                elif secao == "SGI":
                    jql_base += ' AND project = SGI'
            
            # Buscar issues para extrair assignees únicos
            issues = await self._buscar_issues_paginacao(jql_base, fields=["assignee"])
            
            # Extrair assignees únicos
            assignees = {}
            for issue in issues:
                assignee = issue.get("fields", {}).get("assignee")
                if assignee:
                    account_id = assignee.get("accountId")
                    display_name = assignee.get("displayName", "Unknown")
                    if account_id and account_id not in assignees:
                        assignees[account_id] = {
                            "account_id": account_id,
                            "display_name": display_name,
                            "email": assignee.get("emailAddress", "")
                        }
            
            logger.info(f"[RECURSOS_DISPONIVEIS] {len(assignees)} recursos encontrados para seção {secao}")
            return list(assignees.values())
            
        except Exception as e:
            logger.error(f"[RECURSOS_DISPONIVEIS_ERROR] Erro ao buscar recursos: {str(e)}")
            return []
