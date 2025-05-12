from fastapi import APIRouter, HTTPException, Depends
from starlette import status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.item_dtos import ItemDTO, ItemCreateDTO, ItemUpdateDTO
from app.application.services.item_service import ItemService
from app.infrastructure.repositories.sqlalchemy_item_repository import SQLAlchemyItemRepository
from app.db.session import get_async_db

router = APIRouter()

# Dependency for ItemService using SQLAlchemy repository
async def get_item_service(db: AsyncSession = Depends(get_async_db)) -> ItemService:
    item_repository = SQLAlchemyItemRepository(db_session=db)
    return ItemService(item_repository=item_repository)

@router.get("/{item_id}", response_model=ItemDTO)
async def get_item(item_id: int, service: ItemService = Depends(get_item_service)):
    item = await service.get_item_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item

@router.get("/", response_model=List[ItemDTO])
async def get_all_items(service: ItemService = Depends(get_item_service)):
    return await service.get_all_items()

@router.post("/", response_model=ItemDTO, status_code=status.HTTP_201_CREATED)
async def create_item(item_create_dto: ItemCreateDTO, service: ItemService = Depends(get_item_service)):
    return await service.create_item(item_create_dto)

@router.put("/{item_id}", response_model=ItemDTO)
async def update_item(item_id: int, item_update_dto: ItemUpdateDTO, service: ItemService = Depends(get_item_service)):
    item = await service.update_item(item_id, item_update_dto)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item

@router.delete("/{item_id}", response_model=ItemDTO)
async def delete_item(item_id: int, service: ItemService = Depends(get_item_service)):
    item = await service.delete_item(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item
