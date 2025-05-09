from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete

from app.domain.models.item_model import Item as DomainItem
from app.application.dtos.item_dtos import ItemCreateDTO, ItemUpdateDTO
from app.domain.repositories.item_repository import ItemRepository
from app.infrastructure.database.item_sql_model import ItemSQL

class SQLAlchemyItemRepository(ItemRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, item_id: int) -> Optional[DomainItem]:
        result = await self.db_session.execute(select(ItemSQL).filter(ItemSQL.id == item_id))
        item_sql = result.scalars().first()
        if item_sql:
            return DomainItem(id=item_sql.id, description=item_sql.description)
        return None

    async def get_all(self) -> List[DomainItem]:
        result = await self.db_session.execute(select(ItemSQL))
        items_sql = result.scalars().all()
        return [DomainItem(id=item.id, description=item.description) for item in items_sql]

    async def create(self, item_create_dto: ItemCreateDTO) -> DomainItem:
        new_item_sql = ItemSQL(description=item_create_dto.description)
        self.db_session.add(new_item_sql)
        await self.db_session.commit()
        await self.db_session.refresh(new_item_sql)
        return DomainItem(id=new_item_sql.id, description=new_item_sql.description)

    async def update(self, item_id: int, item_update_dto: ItemUpdateDTO) -> Optional[DomainItem]:
        stmt = (
            sqlalchemy_update(ItemSQL)
            .where(ItemSQL.id == item_id)
            .values(description=item_update_dto.description)
            .returning(ItemSQL)
        )
        result = await self.db_session.execute(stmt)
        updated_item_sql = result.scalars().first()
        await self.db_session.commit()
        if updated_item_sql:
            return DomainItem(id=updated_item_sql.id, description=updated_item_sql.description)
        return None

    async def delete(self, item_id: int) -> Optional[DomainItem]:
        item_to_delete = await self.get_by_id(item_id) # Get domain item before deleting
        if not item_to_delete:
            return None
        
        stmt = sqlalchemy_delete(ItemSQL).where(ItemSQL.id == item_id)
        await self.db_session.execute(stmt)
        await self.db_session.commit()
        return item_to_delete

