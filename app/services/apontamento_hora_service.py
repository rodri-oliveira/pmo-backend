from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
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
    def __init__(self, db: Session):
        self.db = db
        self.repository = ApontamentoRepository(db)
        self.recurso_repository = RecursoRepository(db)
        self.projeto_repository = ProjetoRepository(db)
    
    def create_manual(self, apontamento_data: ApontamentoCreateSchema, admin_id: int) -> ApontamentoResponseSchema:
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
        recurso = self.recurso_repository.get(apontamento_data.recurso_id)
        if not recurso:
            raise ValueError(f"Recurso com ID {apontamento_data.recurso_id} não encontrado")
        
        # Verificar se o projeto existe
        projeto = self.projeto_repository.get(apontamento_data.projeto_id)
        if not projeto:
            raise ValueError(f"Projeto com ID {apontamento_data.projeto_id} não encontrado")
        
        # Preparar dados adicionais
        # Fonte é sempre MANUAL para apontamentos criados pelo Admin
        apontamento_dict = apontamento_data.dict()
        apontamento_dict["fonte_apontamento"] = FonteApontamento.MANUAL
        apontamento_dict["id_usuario_admin_criador"] = admin_id
        
        # Criar o apontamento
        apontamento = self.repository.create_manual(apontamento_dict)
        return ApontamentoResponseSchema.from_orm(apontamento)
    
    def get(self, id: int) -> Optional[ApontamentoResponseSchema]:
        """
        Obtém um apontamento pelo ID.
        
        Args:
            id: ID do apontamento
            
        Returns:
            ApontamentoResponseSchema: Dados do apontamento, ou None se não encontrado
        """
        apontamento = self.repository.get(id)
        if not apontamento:
            return None
        return ApontamentoResponseSchema.from_orm(apontamento)
    
    def list_with_filters(self, filtros: ApontamentoFilterSchema, skip: int = 0, limit: int = 100) -> List[ApontamentoResponseSchema]:
        """
        Lista apontamentos com filtros avançados.
        
        Args:
            filtros: Filtros a serem aplicados
            skip: Registros para pular (paginação)
            limit: Limite de registros (paginação)
            
        Returns:
            List[ApontamentoResponseSchema]: Lista de apontamentos
        """
        apontamentos = self.repository.find_with_filters(
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
    
    def get_agregacoes(self, filtros: ApontamentoFilterSchema, 
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
        agregacoes = self.repository.find_with_filters_and_aggregate(
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
        return [ApontamentoAggregationSchema(**agg) for agg in agregacoes]
    
    def update_manual(self, id: int, apontamento: ApontamentoUpdateSchema) -> ApontamentoResponseSchema:
        """Atualiza um apontamento manual"""
        # Implementação stub
        raise ValueError("fonte_apontamento é JIRA, não é permitido editar")
    
    def delete_manual(self, id: int) -> None:
        """Remove um apontamento manual"""
        # Implementação stub
        pass 