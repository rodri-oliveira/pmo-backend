from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import date
from app.models.schemas import FonteApontamento

# Definir tipo genérico para usar nas interfaces
T = TypeVar('T')
ID = TypeVar('ID')

class RepositoryInterface(Generic[T, ID], ABC):
    """Interface base para repositórios."""
    
    @abstractmethod
    def get(self, id: ID) -> Optional[T]:
        """Obtém uma entidade pelo ID."""
        pass
    
    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Lista entidades com paginação e filtros opcionais."""
        pass
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> T:
        """Cria uma nova entidade."""
        pass
    
    @abstractmethod
    def update(self, id: ID, data: Dict[str, Any]) -> T:
        """Atualiza uma entidade existente."""
        pass
    
    @abstractmethod
    def delete(self, id: ID) -> None:
        """Remove uma entidade (pode ser exclusão lógica)."""
        pass

class SecaoRepositoryInterface(RepositoryInterface[T, ID], ABC):
    """Interface para repositório de seções."""
    
    @abstractmethod
    def get_by_nome(self, nome: str) -> Optional[T]:
        """Obtém uma seção pelo nome."""
        pass

class EquipeRepositoryInterface(RepositoryInterface[T, ID], ABC):
    """Interface para repositório de equipes."""
    
    @abstractmethod
    def get_by_nome_and_secao(self, nome: str, secao_id: int) -> Optional[T]:
        """Obtém uma equipe pelo nome e seção."""
        pass
    
    @abstractmethod
    def list_by_secao(self, secao_id: int) -> List[T]:
        """Lista equipes de uma seção."""
        pass

class RecursoRepositoryInterface(RepositoryInterface[T, ID], ABC):
    """Interface para repositório de recursos."""
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[T]:
        """Obtém um recurso pelo email."""
        pass
    
    @abstractmethod
    def get_by_matricula(self, matricula: str) -> Optional[T]:
        """Obtém um recurso pela matrícula."""
        pass
    
    @abstractmethod
    def get_by_jira_user_id(self, jira_user_id: str) -> Optional[T]:
        """Obtém um recurso pelo ID de usuário do Jira."""
        pass
    
    @abstractmethod
    def list_by_equipe(self, equipe_id: int) -> List[T]:
        """Lista recursos de uma equipe."""
        pass

class ProjetoRepositoryInterface(RepositoryInterface[T, ID], ABC):
    """Interface para repositório de projetos."""
    
    @abstractmethod
    def get_by_codigo_empresa(self, codigo_empresa: str) -> Optional[T]:
        """Obtém um projeto pelo código da empresa."""
        pass
    
    @abstractmethod
    def get_by_jira_project_key(self, jira_project_key: str) -> Optional[T]:
        """Obtém um projeto pela chave do projeto no Jira."""
        pass
    
    @abstractmethod
    def list_by_status(self, status_id: int) -> List[T]:
        """Lista projetos com um determinado status."""
        pass

class ApontamentoRepositoryInterface(RepositoryInterface[T, ID], ABC):
    """Interface para repositório de apontamentos."""
    
    @abstractmethod
    def create_manual(self, data: Dict[str, Any]) -> T:
        """Cria um apontamento manual."""
        pass
    
    @abstractmethod
    def update_manual(self, id: ID, data: Dict[str, Any]) -> T:
        """Atualiza um apontamento manual."""
        pass
    
    @abstractmethod
    def delete_manual(self, id: ID) -> None:
        """Remove um apontamento manual."""
        pass
    
    @abstractmethod
    def sync_jira_apontamento(self, data: Dict[str, Any]) -> T:
        """Sincroniza um apontamento do Jira (cria ou atualiza)."""
        pass
    
    @abstractmethod
    def delete_from_jira(self, jira_worklog_id: str) -> None:
        """Remove um apontamento com base no ID do worklog do Jira."""
        pass
    
    @abstractmethod
    def get_by_jira_worklog_id(self, jira_worklog_id: str) -> Optional[T]:
        """Obtém um apontamento pelo ID do worklog do Jira."""
        pass
    
    @abstractmethod
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
                       ) -> List[T]:
        """Busca apontamentos com filtros avançados."""
        pass
    
    @abstractmethod
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
        pass 