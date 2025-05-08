from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.status_projeto_model import StatusProjeto
from app.application.dtos.status_projeto_dtos import StatusProjetoCreateDTO, StatusProjetoUpdateDTO

class StatusProjetoRepository(ABC):
    @abstractmethod
    async def get_by_id(self, status_id: int) -> Optional[StatusProjeto]:
        pass

    @abstractmethod
    async def get_by_nome(self, nome: str) -> Optional[StatusProjeto]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[StatusProjeto]:
        pass

    @abstractmethod
    async def create(self, status_create_dto: StatusProjetoCreateDTO) -> StatusProjeto:
        pass

    @abstractmethod
    async def update(self, status_id: int, status_update_dto: StatusProjetoUpdateDTO) -> Optional[StatusProjeto]:
        pass

    @abstractmethod
    async def delete(self, status_id: int) -> Optional[StatusProjeto]: # Or just return bool
        pass

