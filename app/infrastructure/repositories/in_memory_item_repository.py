from typing import List, Optional, Dict
from app.domain.models.item_model import Item
from app.application.dtos.item_dtos import ItemCreateDTO, ItemUpdateDTO
from app.domain.repositories.item_repository import ItemRepository

class InMemoryItemRepository(ItemRepository):
    def __init__(self):
        self._items: Dict[int, Item] = {}
        self._current_id: int = 0

    async def get_by_id(self, item_id: int) -> Optional[Item]:
        return self._items.get(item_id)

    async def get_all(self) -> List[Item]:
        return list(self._items.values())

    async def create(self, item_create_dto: ItemCreateDTO) -> Item:
        self._current_id += 1
        item = Item(id=self._current_id, description=item_create_dto.description)
        self._items[self._current_id] = item
        return item

    async def update(self, item_id: int, item_update_dto: ItemUpdateDTO) -> Optional[Item]:
        if item_id not in self._items:
            return None
        item = self._items[item_id]
        item.description = item_update_dto.description
        self._items[item_id] = item
        return item

    async def delete(self, item_id: int) -> Optional[Item]:
        return self._items.pop(item_id, None)

