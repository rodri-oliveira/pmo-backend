from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy import func, extract, and_, or_
from sqlalchemy.orm import Session, joinedload, aliased
from app.db.orm_models import Apontamento, Recurso, Projeto, Equipe, Secao, FonteApontamento
from app.repositories.base_repository import BaseRepository

class ApontamentoRepository(BaseRepository[Apontamento, int]):
    """Repositório para operações com a entidade Apontamento."""
    
    def __init__(self, db: Session):
        super().__init__(db, Apontamento)
    
    def create_manual(self, data: Dict[str, Any]) -> Apontamento:
        """
        Cria um apontamento manual.
        Garante que fonte_apontamento='MANUAL' e que id_usuario_admin_criador esteja presente.
        """
        # Garantir que a fonte é MANUAL
        data["fonte_apontamento"] = FonteApontamento.MANUAL
        
        # Verificar se id_usuario_admin_criador está presente
        if "id_usuario_admin_criador" not in data or data["id_usuario_admin_criador"] is None:
            raise ValueError("id_usuario_admin_criador é obrigatório para apontamentos manuais")
        
        return self.create(data)
    
    def update_manual(self, id: int, data: Dict[str, Any]) -> Apontamento:
        """
        Atualiza um apontamento manual.
        Verifica se o apontamento é do tipo MANUAL antes de atualizar.
        """
        # Obter o apontamento
        apontamento = self.get(id)
        if apontamento is None:
            raise ValueError(f"Apontamento com ID {id} não encontrado")
        
        # Verificar se é um apontamento MANUAL
        if apontamento.fonte_apontamento != FonteApontamento.MANUAL:
            raise ValueError(
                f"Apontamento com fonte_apontamento={apontamento.fonte_apontamento} "
                f"não pode ser editado, apenas apontamentos MANUAL são editáveis"
            )
        
        # Não permitir alterar a fonte do apontamento
        if "fonte_apontamento" in data:
            del data["fonte_apontamento"]
        
        # Atualizar
        return self.update(id, data)
    
    def delete_manual(self, id: int) -> None:
        """
        Remove um apontamento manual.
        Verifica se o apontamento é do tipo MANUAL antes de remover.
        """
        # Obter o apontamento
        apontamento = self.get(id)
        if apontamento is None:
            raise ValueError(f"Apontamento com ID {id} não encontrado")
        
        # Verificar se é um apontamento MANUAL
        if apontamento.fonte_apontamento != FonteApontamento.MANUAL:
            raise ValueError(
                f"Apontamento com fonte_apontamento={apontamento.fonte_apontamento} "
                f"não pode ser removido, apenas apontamentos MANUAL são removíveis"
            )
        
        # Remover
        self.db.delete(apontamento)
        self.db.commit()
    
    def get_by_jira_worklog_id(self, jira_worklog_id: str) -> Optional[Apontamento]:
        """Obtém um apontamento pelo ID do worklog do Jira."""
        return self.db.query(Apontamento).filter(Apontamento.jira_worklog_id == jira_worklog_id).first()
    
    def sync_jira_apontamento(self, data: Dict[str, Any]) -> Apontamento:
        """
        Sincroniza um apontamento do Jira (cria ou atualiza).
        Garante que fonte_apontamento='JIRA'.
        """
        # Garantir que a fonte é JIRA
        data["fonte_apontamento"] = FonteApontamento.JIRA
        
        # Verificar se já existe um apontamento com este jira_worklog_id
        jira_worklog_id = data.get("jira_worklog_id")
        if not jira_worklog_id:
            raise ValueError("jira_worklog_id é obrigatório para apontamentos do Jira")
        
        existing = self.get_by_jira_worklog_id(jira_worklog_id)
        
        if existing:
            # Atualizar apontamento existente
            # Não usar update_manual pois queremos atualizar mesmo sendo JIRA
            for key, value in data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Criar novo apontamento
            return self.create(data)
    
    def delete_from_jira(self, jira_worklog_id: str) -> None:
        """
        Remove um apontamento com base no ID do worklog do Jira.
        """
        apontamento = self.get_by_jira_worklog_id(jira_worklog_id)
        if apontamento:
            self.db.delete(apontamento)
            self.db.commit()
    
    def find_with_filters(self, 
                        recurso_id: Optional[int] = None,
                        projeto_id: Optional[int] = None,
                        equipe_id: Optional[int] = None,
                        secao_id: Optional[int] = None,
                        data_inicio: Optional[date] = None,
                        data_fim: Optional[date] = None,
                        fonte_apontamento: Optional[FonteApontamento] = None,
                        jira_issue_key: Optional[str] = None,
                        skip: int = 0,
                        limit: int = 100
                       ) -> List[Apontamento]:
        """Busca apontamentos com filtros avançados."""
        query = self.db.query(Apontamento).options(
            joinedload(Apontamento.recurso),
            joinedload(Apontamento.projeto)
        )
        
        # Aplicar filtros diretos
        if recurso_id:
            query = query.filter(Apontamento.recurso_id == recurso_id)
        
        if projeto_id:
            query = query.filter(Apontamento.projeto_id == projeto_id)
        
        if data_inicio:
            query = query.filter(Apontamento.data_apontamento >= data_inicio)
        
        if data_fim:
            query = query.filter(Apontamento.data_apontamento <= data_fim)
        
        if fonte_apontamento:
            query = query.filter(Apontamento.fonte_apontamento == fonte_apontamento)
        
        if jira_issue_key:
            query = query.filter(Apontamento.jira_issue_key.ilike(f"%{jira_issue_key}%"))
        
        # Filtros relacionais
        if equipe_id or secao_id:
            query = query.join(Apontamento.recurso)
            
            if equipe_id:
                query = query.filter(Recurso.equipe_principal_id == equipe_id)
            
            if secao_id:
                query = query.join(Recurso.equipe_principal).filter(Equipe.secao_id == secao_id)
        
        # Aplicar paginação
        return query.order_by(Apontamento.data_apontamento.desc()).offset(skip).limit(limit).all()
    
    def find_with_filters_and_aggregate(self,
                                      recurso_id: Optional[int] = None,
                                      projeto_id: Optional[int] = None,
                                      equipe_id: Optional[int] = None,
                                      secao_id: Optional[int] = None,
                                      data_inicio: Optional[date] = None,
                                      data_fim: Optional[date] = None,
                                      fonte_apontamento: Optional[FonteApontamento] = None,
                                      agrupar_por_recurso: bool = False,
                                      agrupar_por_projeto: bool = False,
                                      agrupar_por_data: bool = False,
                                      agrupar_por_mes: bool = False
                                     ) -> List[Dict[str, Any]]:
        """Busca apontamentos com filtros e agrega os resultados."""
        # Colunas para select e group by
        select_columns = [
            func.sum(Apontamento.horas_apontadas).label("total_horas"),
            func.count(Apontamento.id).label("total_registros")
        ]
        
        group_by_columns = []
        
        # Adicionar colunas conforme configuração de agrupamento
        if agrupar_por_recurso:
            select_columns.append(Apontamento.recurso_id.label("recurso_id"))
            group_by_columns.append(Apontamento.recurso_id)
        
        if agrupar_por_projeto:
            select_columns.append(Apontamento.projeto_id.label("projeto_id"))
            group_by_columns.append(Apontamento.projeto_id)
        
        if agrupar_por_data:
            select_columns.append(Apontamento.data_apontamento.label("data_apontamento"))
            group_by_columns.append(Apontamento.data_apontamento)
        
        if agrupar_por_mes:
            select_columns.extend([
                extract('year', Apontamento.data_apontamento).label("ano"),
                extract('month', Apontamento.data_apontamento).label("mes")
            ])
            group_by_columns.extend([
                extract('year', Apontamento.data_apontamento),
                extract('month', Apontamento.data_apontamento)
            ])
        
        # Se não há colunas para agrupar, usar apenas totais gerais
        if not group_by_columns:
            query = self.db.query(*select_columns)
        else:
            query = self.db.query(*select_columns)
        
        # Aplicar filtros
        if recurso_id:
            query = query.filter(Apontamento.recurso_id == recurso_id)
        
        if projeto_id:
            query = query.filter(Apontamento.projeto_id == projeto_id)
        
        if data_inicio:
            query = query.filter(Apontamento.data_apontamento >= data_inicio)
        
        if data_fim:
            query = query.filter(Apontamento.data_apontamento <= data_fim)
        
        if fonte_apontamento:
            query = query.filter(Apontamento.fonte_apontamento == fonte_apontamento)
        
        # Filtros relacionais
        if equipe_id or secao_id:
            query = query.join(Apontamento.recurso)
            
            if equipe_id:
                query = query.filter(Recurso.equipe_principal_id == equipe_id)
            
            if secao_id:
                query = query.join(Recurso.equipe_principal).filter(Equipe.secao_id == secao_id)
        
        # Aplicar agrupamento
        if group_by_columns:
            query = query.group_by(*group_by_columns)
        
        # Ordenar pelos campos de agrupamento
        if agrupar_por_mes:
            query = query.order_by("ano", "mes")
        elif agrupar_por_data:
            query = query.order_by(Apontamento.data_apontamento)
        
        # Executar a consulta e converter para dicionários
        result = query.all()
        
        # Converter resultado para lista de dicionários
        return [dict(zip([c['name'] for c in result.keys()], row)) for row in result] 