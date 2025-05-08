from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy import func, extract, and_, or_, text
from sqlalchemy.orm import Session, joinedload
from app.db.orm_models import Apontamento, Recurso, Projeto, Equipe, Secao, FonteApontamento
from app.repositories.base_repository import BaseRepository

class ApontamentoRepository(BaseRepository[Apontamento]):
    """
    Repositório para operações específicas de apontamentos de horas.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o repositório com uma sessão do banco de dados.
        
        Args:
            db: Sessão do banco de dados
        """
        super().__init__(db, Apontamento)
    
    def get_by_jira_worklog_id(self, jira_worklog_id: str) -> Optional[Apontamento]:
        """Obtém um apontamento pelo ID do worklog do Jira."""
        return self.db.query(Apontamento).filter(Apontamento.jira_worklog_id == jira_worklog_id).first()
    
    def create_manual(self, data: Dict[str, Any], admin_id: int) -> Apontamento:
        """
        Cria um apontamento manual feito por um administrador.
        
        Args:
            data: Dados do apontamento
            admin_id: ID do administrador que está criando o apontamento
            
        Returns:
            Apontamento criado
        """
        apontamento_data = {
            **data,
            "fonte_apontamento": "MANUAL",
            "id_usuario_admin_criador": admin_id
        }
        return self.create(apontamento_data)
    
    def update_manual(self, id: int, data: Dict[str, Any]) -> Optional[Apontamento]:
        """
        Atualiza um apontamento manual.
        
        Args:
            id: ID do apontamento
            data: Dados atualizados
            
        Returns:
            Apontamento atualizado ou None se não encontrado ou não for manual
        """
        apontamento = self.get(id)
        if apontamento is None or apontamento.fonte_apontamento != "MANUAL":
            return None
            
        return self.update(id, data)
    
    def delete_manual(self, id: int) -> bool:
        """
        Remove um apontamento manual.
        
        Args:
            id: ID do apontamento
            
        Returns:
            True se removido com sucesso, False se não encontrado ou não for manual
        """
        apontamento = self.get(id)
        if apontamento is None or apontamento.fonte_apontamento != "MANUAL":
            return False
            
        return self.delete(id)
    
    def sync_jira_apontamento(self, jira_worklog_id: str, data: Dict[str, Any]) -> Apontamento:
        """
        Cria ou atualiza um apontamento a partir de dados do Jira.
        
        Args:
            jira_worklog_id: ID do worklog no Jira
            data: Dados do apontamento
            
        Returns:
            Apontamento criado ou atualizado
        """
        apontamento = self.db.query(self.model).filter(
            self.model.jira_worklog_id == jira_worklog_id
        ).first()
        
        apontamento_data = {
            **data,
            "fonte_apontamento": "JIRA",
            "jira_worklog_id": jira_worklog_id
        }
        
        if apontamento:
            # Atualiza o apontamento existente
            for key, value in apontamento_data.items():
                setattr(apontamento, key, value)
                
            self.db.commit()
            self.db.refresh(apontamento)
            return apontamento
        else:
            # Cria um novo apontamento
            apontamento = self.model(**apontamento_data)
            self.db.add(apontamento)
            self.db.commit()
            self.db.refresh(apontamento)
            return apontamento
    
    def delete_from_jira(self, jira_worklog_id: str) -> bool:
        """
        Remove um apontamento com base no ID do worklog do Jira.
        
        Args:
            jira_worklog_id: ID do worklog no Jira
            
        Returns:
            True se removido com sucesso, False se não encontrado
        """
        apontamento = self.db.query(self.model).filter(
            self.model.jira_worklog_id == jira_worklog_id
        ).first()
        
        if apontamento is None:
            return False
            
        self.db.delete(apontamento)
        self.db.commit()
        return True
    
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
        query = self.db.query(Apontamento)
        
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
        
        # Filtros relacionais (equipe e seção)
        if equipe_id or secao_id:
            query = query.join(Apontamento.recurso)
            
            if equipe_id:
                query = query.filter(Recurso.equipe_principal_id == equipe_id)
            
            if secao_id:
                query = query.join(Recurso.equipe_principal).filter(Equipe.secao_id == secao_id)
        
        # Aplicar paginação e ordenação
        return query.order_by(Apontamento.data_apontamento.desc()).offset(skip).limit(limit).all()
    
    def find_with_filters_and_aggregate(
        self,
        recurso_id: Optional[int] = None,
        projeto_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        fonte_apontamento: Optional[str] = None,
        jira_issue_key: Optional[str] = None,
        aggregate: bool = False
    ) -> Dict[str, Any]:
        """
        Busca apontamentos com filtros avançados e opcionalmente agrega horas.
        
        Args:
            recurso_id: Filtro por recurso
            projeto_id: Filtro por projeto
            equipe_id: Filtro por equipe do recurso
            secao_id: Filtro por seção do recurso
            data_inicio: Data inicial do período
            data_fim: Data final do período
            fonte_apontamento: Filtro por fonte (MANUAL ou JIRA)
            jira_issue_key: Filtro por chave de issue no Jira
            aggregate: Se True, inclui agregações de horas
            
        Returns:
            Dicionário com resultados e agregações
        """
        query = self.db.query(self.model)
        
        # Aplicar filtros
        if recurso_id:
            query = query.filter(self.model.recurso_id == recurso_id)
            
        if projeto_id:
            query = query.filter(self.model.projeto_id == projeto_id)
            
        if equipe_id:
            query = query.join(Recurso).filter(Recurso.equipe_id == equipe_id)
            
        if secao_id:
            query = query.join(Recurso).filter(Recurso.secao_id == secao_id)
            
        if data_inicio:
            query = query.filter(self.model.data_apontamento >= data_inicio)
            
        if data_fim:
            query = query.filter(self.model.data_apontamento <= data_fim)
            
        if fonte_apontamento:
            query = query.filter(self.model.fonte_apontamento == fonte_apontamento)
            
        if jira_issue_key:
            query = query.filter(self.model.jira_issue_key == jira_issue_key)
            
        result = {
            "apontamentos": query.all()
        }
        
        # Calcular agregações se solicitado
        if aggregate:
            total_horas = self.db.query(
                func.sum(self.model.horas_apontadas)
            ).filter(
                *[c for c in query.whereclause.clauses]
            ).scalar() or 0
            
            result["agregacoes"] = {
                "total_horas": total_horas
            }
            
        return result 