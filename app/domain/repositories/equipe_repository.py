from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.equipe_model import Equipe
from app.application.dtos.equipe_dtos import EquipeCreateDTO, EquipeUpdateDTO

class EquipeRepository(ABC):
    @abstractmethod
    async def get_by_id(self, equipe_id: int) -> Optional[Equipe]:
        pass

    @abstractmethod
    async def get_by_nome_and_secao_id(self, nome: str, secao_id: int) -> Optional[Equipe]:
        pass

    @abstractmethod
    async def get_all_by_secao_id(self, secao_id: int, skip: int = 0, limit: int = 100, apenas_ativos: bool = False) -> List[Equipe]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False) -> List[Equipe]:
        pass

    @abstractmethod
    async def create(self, equipe_create_dto: EquipeCreateDTO) -> Equipe:
        pass

    @abstractmethod
    async def update(self, equipe_id: int, equipe_update_dto: EquipeUpdateDTO) -> Optional[Equipe]:
        pass

    @abstractmethod
    async def delete(self, equipe_id: int) -> Optional[Equipe]:
        pass

