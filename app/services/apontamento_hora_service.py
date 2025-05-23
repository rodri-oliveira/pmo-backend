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