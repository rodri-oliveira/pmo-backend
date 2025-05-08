from typing import List, Optional
from app.domain.models.item_model import Item
from app.application.dtos.item_dtos import ItemCreateDTO, ItemUpdateDTO, ItemDTO
from app.domain.repositories.item_repository import ItemRepository

class ItemService:
    def __init__(self, item_repository: ItemRepository):
        self.item_repository = item_repository

    async def get_item_by_id(self, item_id: int) -> Optional[ItemDTO]:
        item = await self.item_repository.get_by_id(item_id)
        if item:
            return ItemDTO(id=item.id, description=item.description)
        return None

    async def get_all_items(self) -> List[ItemDTO]:
        items = await self.item_repository.get_all()
        return [ItemDTO(id=item.id, description=item.description) for item in items]

    async def create_item(self, item_create_dto: ItemCreateDTO) -> ItemDTO:
        item = await self.item_repository.create(item_create_dto)
        return ItemDTO(id=item.id, description=item.description)

    async def update_item(self, item_id: int, item_update_dto: ItemUpdateDTO) -> Optional[ItemDTO]:
        item = await self.item_repository.update(item_id, item_update_dto)
        if item:
            return ItemDTO(id=item.id, description=item.description)
        return None

    async def delete_item(self, item_id: int) -> Optional[ItemDTO]:
        item = await self.item_repository.delete(item_id)
        if item:
            return ItemDTO(id=item.id, description=item.description)
        return None

