from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dtos.apontamento_schema import (
    ApontamentoCreateSchema,
    ApontamentoUpdateSchema,
    ApontamentoFilterSchema,
    ApontamentoResponseSchema,
    ApontamentoAggregationSchema,
    FonteApontamento
)
from app.repositories.apontamento_repository import ApontamentoRepository
from app.repositories.recurso_repository import RecursoRepository
from app.repositories.projeto_repository import ProjetoRepository

class ApontamentoHoraService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ApontamentoRepository(db)
        self.recurso_repository = RecursoRepository(db)
        self.projeto_repository = ProjetoRepository(db)
    
    async def create_manual(self, apontamento_data: ApontamentoCreateSchema, admin_id: int) -> ApontamentoResponseSchema:
        """
        Cria um apontamento manual pelo Admin.
        
        Args:
            apontamento_data: Dados do apontamento
            admin_id: ID do usuário admin que está criando o apontamento
            
        Returns:
            ApontamentoResponseSchema: Dados do apontamento criado
            
        Raises:
            ValueError: Se houver erro de validação
        """
        # Verificar se o recurso existe
        recurso = await self.recurso_repository.get(apontamento_data.recurso_id)
        if not recurso:
            raise ValueError(f"Recurso com ID {apontamento_data.recurso_id} não encontrado")
        
        # Verificar se o projeto existe
        projeto = await self.projeto_repository.get(apontamento_data.projeto_id)
        if not projeto:
            raise ValueError(f"Projeto com ID {apontamento_data.projeto_id} não encontrado")
        
        # Preparar dados adicionais
        # Fonte é sempre MANUAL para apontamentos criados pelo Admin
        apontamento_dict = apontamento_data.dict()
        apontamento_dict["fonte_apontamento"] = FonteApontamento.MANUAL
        apontamento_dict["id_usuario_admin_criador"] = admin_id
        
        # Remover timezone de todos os campos datetime (se houver)
        for campo in ["data_hora_inicio_trabalho", "data_criacao", "data_atualizacao", "data_sincronizacao_jira"]:
            valor = apontamento_dict.get(campo)
            if isinstance(valor, datetime) and valor.tzinfo is not None:
                apontamento_dict[campo] = valor.replace(tzinfo=None)
        
        # Criar o apontamento
        apontamento = await self.repository.create_manual(apontamento_dict, admin_id)
        return ApontamentoResponseSchema.from_orm(apontamento)
    
    async def get(self, id: int) -> Optional[ApontamentoResponseSchema]:
        """
        Obtém um apontamento pelo ID.
        
        Args:
            id: ID do apontamento
            
        Returns:
            ApontamentoResponseSchema: Dados do apontamento, ou None se não encontrado
        """
        apontamento = await self.repository.get(id)
        if not apontamento:
            return None
        return ApontamentoResponseSchema.from_orm(apontamento)
    
    async def list_with_filters(self, filtros: ApontamentoFilterSchema, skip: int = 0, limit: int = 100) -> List[ApontamentoResponseSchema]:
        """
        Lista apontamentos com filtros avançados.
        
        Args:
            filtros: Filtros a serem aplicados
            skip: Registros para pular (paginação)
            limit: Limite de registros (paginação)
            
        Returns:
            List[ApontamentoResponseSchema]: Lista de apontamentos
        """
        apontamentos = await self.repository.find_with_filters(
            recurso_id=filtros.recurso_id,
            projeto_id=filtros.projeto_id,
            equipe_id=filtros.equipe_id,
            secao_id=filtros.secao_id,
            data_inicio=filtros.data_inicio,
            data_fim=filtros.data_fim,
            fonte_apontamento=filtros.fonte_apontamento,
            jira_issue_key=filtros.jira_issue_key,
            skip=skip,
            limit=limit
        )
        return [ApontamentoResponseSchema.from_orm(a) for a in apontamentos]
    
    async def get_agregacoes(self, filtros: ApontamentoFilterSchema, 
                      agrupar_por_recurso: bool, 
                      agrupar_por_projeto: bool,
                      agrupar_por_data: bool,
                      agrupar_por_mes: bool) -> List[ApontamentoAggregationSchema]:
        """
        Obtém agregações (soma de horas) dos apontamentos com filtros.
        
        Args:
            filtros: Filtros a serem aplicados
            agrupar_por_recurso: Se deve agrupar por recurso
            agrupar_por_projeto: Se deve agrupar por projeto
            agrupar_por_data: Se deve agrupar por data
            agrupar_por_mes: Se deve agrupar por mês/ano
            
        Returns:
            List[ApontamentoAggregationSchema]: Lista de agregações
        """
        import logging
        logger = logging.getLogger("app.services.apontamento_hora_service")
        agregacoes = await self.repository.find_with_filters_and_aggregate(
            recurso_id=filtros.recurso_id,
            projeto_id=filtros.projeto_id,
            equipe_id=filtros.equipe_id,
            secao_id=filtros.secao_id,
            data_inicio=filtros.data_inicio,
            data_fim=filtros.data_fim,
            fonte_apontamento=filtros.fonte_apontamento,
            agrupar_por_recurso=agrupar_por_recurso,
            agrupar_por_projeto=agrupar_por_projeto,
            agrupar_por_data=agrupar_por_data,
            agrupar_por_mes=agrupar_por_mes
        )
        try:
            # O repositório retorna um dicionário com 'items', precisamos retornar uma lista de dicts
            items = agregacoes.get('items', []) if isinstance(agregacoes, dict) else agregacoes
            return [ApontamentoAggregationSchema(**agg) for agg in items]
        except Exception as e:
            logger.error(f"[get_agregacoes] Erro ao converter agregações: {str(e)} | agregacoes={agregacoes}", exc_info=True)
            raise
    
    async def update_manual(self, id: int, apontamento: ApontamentoUpdateSchema) -> ApontamentoResponseSchema:
        """
        Atualiza um apontamento manual.
        
        Args:
            id: ID do apontamento a ser atualizado
            apontamento: Dados para atualização
            
        Returns:
            ApontamentoResponseSchema: Dados do apontamento atualizado
            
        Raises:
            ValueError: Se o apontamento não for do tipo MANUAL ou se houver erro de validação
        """
        # Verificar se o apontamento existe e é do tipo MANUAL
        apontamento_atual = await self.repository.get(id)
        if not apontamento_atual:
            raise ValueError(f"Apontamento com ID {id} não encontrado")
            
        if apontamento_atual.fonte_apontamento != FonteApontamento.MANUAL:
            raise ValueError(f"Apenas apontamentos do tipo MANUAL podem ser editados. Este apontamento é do tipo {apontamento_atual.fonte_apontamento}")
            
        # Remover timezone de todos os campos datetime (se houver)
        apontamento_dict = apontamento.dict(exclude_unset=True)
        from datetime import datetime
        for campo in ["data_hora_inicio_trabalho", "data_criacao", "data_atualizacao", "data_sincronizacao_jira"]:
            valor = apontamento_dict.get(campo)
            if isinstance(valor, datetime) and valor.tzinfo is not None:
                apontamento_dict[campo] = valor.replace(tzinfo=None)
        # Atualizar o apontamento
        apontamento_atualizado = await self.repository.update_manual(id, apontamento_dict)
        return ApontamentoResponseSchema.from_orm(apontamento_atualizado)
    
    async def delete_manual(self, id: int) -> None:
        """
        Remove um apontamento manual.
        
        Args:
            id: ID do apontamento a ser removido
            
        Raises:
            ValueError: Se o apontamento não for do tipo MANUAL ou se houver erro
        """
        # Verificar se o apontamento existe e é do tipo MANUAL
        apontamento = await self.repository.get(id)
        if not apontamento:
            raise ValueError(f"Apontamento com ID {id} não encontrado")
            
        if apontamento.fonte_apontamento != FonteApontamento.MANUAL:
            raise ValueError(f"Apenas apontamentos do tipo MANUAL podem ser removidos. Este apontamento é do tipo {apontamento.fonte_apontamento}")
            
        # Remover o apontamento
        await self.repository.delete(id)
        
    async def processar_worklog_jira(self, worklog: dict) -> None:
        """
        Processa um worklog do Jira e salva como apontamento.
        
        Args:
            worklog: Dados do worklog do Jira
            
        Returns:
            None
        """
        import logging
        from datetime import datetime
        from dateutil import parser
        from app.db.orm_models import FonteApontamento
        
        logger = logging.getLogger("app.services.apontamento_hora_service.processar_worklog_jira")
        
        try:
            # Extrair dados do worklog
            worklog_id = worklog.get("id")
            issue_key = worklog.get("issueKey")
            
            if not worklog_id or not issue_key:
                logger.warning(f"[PROCESSAR_WORKLOG] Worklog sem ID ou issue_key: {worklog}")
                return
                
            # Verificar se já existe um apontamento com este worklog_id
            apontamento_existente = await self.repository.get_by_jira_worklog_id(worklog_id)
            if apontamento_existente:
                logger.info(f"[PROCESSAR_WORKLOG] Worklog {worklog_id} já existe como apontamento {apontamento_existente.id}")
                return
                
            # Extrair dados do autor
            author = worklog.get("author", {})
            author_account_id = author.get("accountId")
            
            # Buscar recurso pelo jira_user_id
            recurso = None
            if author_account_id:
                recurso = await self.recurso_repository.get_by_jira_user_id(author_account_id)
                
            if not recurso:
                logger.warning(f"[PROCESSAR_WORKLOG] Recurso não encontrado para o author {author_account_id}")
                return
                
            # Extrair dados do projeto
            projeto = None
            if issue_key:
                # Extrair o código do projeto da issue (ex: PROJ-123 -> PROJ)
                projeto_key = issue_key.split('-')[0] if '-' in issue_key else None
                if projeto_key:
                    projeto = await self.projeto_repository.get_by_jira_project_key(projeto_key)
                    
            if not projeto:
                logger.warning(f"[PROCESSAR_WORKLOG] Projeto não encontrado para a issue {issue_key}")
                return
                
            # Processar data e tempo
            started = worklog.get("started")
            time_spent_seconds = worklog.get("timeSpentSeconds", 0)
            
            if not started or not time_spent_seconds:
                logger.warning(f"[PROCESSAR_WORKLOG] Worklog sem data ou tempo: {worklog}")
                return
                
            # Converter para datetime
            try:
                data_hora = parser.parse(started)
                data_apontamento = data_hora.date()
            except Exception as e:
                logger.error(f"[PROCESSAR_WORKLOG] Erro ao processar data do worklog: {str(e)}")
                return
                
            # Converter segundos para horas (decimal)
            from decimal import Decimal
            horas_apontadas = Decimal(time_spent_seconds) / Decimal(3600)
            
            # Preparar dados do apontamento
            now = datetime.now()
            
            # Processar o comentário - pode ser string ou objeto ADF
            comment = worklog.get("comment", "")
            descricao = ""
            
            # Verificar se o comentário é um dicionário (formato ADF)
            if isinstance(comment, dict) and "content" in comment:
                # Extrair texto do formato ADF
                try:
                    # Percorrer a estrutura ADF para extrair o texto
                    text_parts = []
                    for content_item in comment.get("content", []):
                        if content_item.get("type") == "paragraph" and "content" in content_item:
                            for text_item in content_item.get("content", []):
                                if text_item.get("type") == "text":
                                    text_parts.append(text_item.get("text", ""))
                    descricao = " ".join(text_parts)
                    logger.info(f"[PROCESSAR_WORKLOG] Extraído texto do formato ADF: {descricao}")
                except Exception as e:
                    logger.warning(f"[PROCESSAR_WORKLOG] Erro ao extrair texto do formato ADF: {str(e)}")
                    # Em caso de erro, converter o objeto para string JSON
                    import json
                    try:
                        descricao = json.dumps(comment)
                    except:
                        descricao = str(comment)
            else:
                # Se for uma string simples, usar diretamente
                descricao = str(comment) if comment else ""
            
            apontamento_data = {
                "recurso_id": recurso.id,
                "projeto_id": projeto.id,
                "jira_issue_key": issue_key,
                "jira_worklog_id": worklog_id,
                "data_hora_inicio_trabalho": data_hora,
                "data_apontamento": data_apontamento,
                "horas_apontadas": horas_apontadas,
                "descricao": descricao,
                "fonte_apontamento": FonteApontamento.JIRA,
                "data_criacao": now,
                "data_atualizacao": now,
                "data_sincronizacao_jira": now
            }
            
            # Criar o apontamento
            await self.repository.sync_jira_apontamento(worklog_id, apontamento_data)
            logger.info(f"[PROCESSAR_WORKLOG] Worklog {worklog_id} processado com sucesso")
            
        except Exception as e:
            logger.error(f"[PROCESSAR_WORKLOG] Erro ao processar worklog: {str(e)}", exc_info=True)