from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.item_model import Item
from app.application.dtos.item_dtos import ItemCreateDTO, ItemUpdateDTO

class ItemRepository(ABC):
    @abstractmethod
    async def get_by_id(self, item_id: int) -> Optional[Item]:
        pass

    @abstractmethod
    async def get_all(self) -> List[Item]:
        pass

    @abstractmethod
    async def create(self, item_create_dto: ItemCreateDTO) -> Item:
        pass

    @abstractmethod
    async def update(self, item_id: int, item_update_dto: ItemUpdateDTO) -> Optional[Item]:
        pass

    @abstractmethod
    async def delete(self, item_id: int) -> Optional[Item]:
        pass

