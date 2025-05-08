from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.secao_model import Secao
from app.application.dtos.secao_dtos import SecaoCreateDTO, SecaoUpdateDTO

class SecaoRepository(ABC):
    @abstractmethod
    async def get_by_id(self, secao_id: int) -> Optional[Secao]:
        pass

    @abstractmethod
    async def get_by_nome(self, nome: str) -> Optional[Secao]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False) -> List[Secao]:
        pass

    @abstractmethod
    async def create(self, secao_create_dto: SecaoCreateDTO) -> Secao:
        pass

    @abstractmethod
    async def update(self, secao_id: int, secao_update_dto: SecaoUpdateDTO) -> Optional[Secao]:
        pass

    @abstractmethod
    async def delete(self, secao_id: int) -> Optional[Secao]: # Or just return bool
        pass

