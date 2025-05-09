from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.recurso_model import Recurso
from app.application.dtos.recurso_dtos import RecursoCreateDTO, RecursoUpdateDTO

class RecursoRepository(ABC):
    @abstractmethod
    async def get_by_id(self, recurso_id: int) -> Optional[Recurso]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Recurso]:
        pass

    @abstractmethod
    async def get_by_matricula(self, matricula: str) -> Optional[Recurso]:
        pass

    @abstractmethod
    async def get_by_jira_user_id(self, jira_user_id: str) -> Optional[Recurso]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False, equipe_id: Optional[int] = None) -> List[Recurso]:
        pass

    @abstractmethod
    async def create(self, recurso_create_dto: RecursoCreateDTO) -> Recurso:
        pass

    @abstractmethod
    async def update(self, recurso_id: int, recurso_update_dto: RecursoUpdateDTO) -> Optional[Recurso]:
        pass

    @abstractmethod
    async def delete(self, recurso_id: int) -> Optional[Recurso]:
        pass

