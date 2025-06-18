from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.projeto_model import Projeto
from app.application.dtos.projeto_dtos import ProjetoCreateDTO, ProjetoUpdateDTO

class ProjetoRepository(ABC):
    @abstractmethod
    async def get_by_id(self, projeto_id: int) -> Optional[Projeto]:
        pass

    @abstractmethod
    async def get_by_nome(self, nome: str) -> Optional[Projeto]:
        pass

    @abstractmethod
    async def get_by_codigo_empresa(self, codigo_empresa: str) -> Optional[Projeto]:
        pass

    @abstractmethod
    async def get_by_jira_project_key(self, jira_project_key: str) -> Optional[Projeto]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False, status_projeto: Optional[int] = None, search: Optional[str] = None) -> List[Projeto]:
        pass

    @abstractmethod
    async def create(self, projeto_create_dto: ProjetoCreateDTO) -> Projeto:
        pass

    @abstractmethod
    async def update(self, projeto_id: int, projeto_update_dto: ProjetoUpdateDTO) -> Optional[Projeto]:
        pass

    @abstractmethod
    async def delete(self, projeto_id: int) -> Optional[Projeto]:
        pass

