# app/utils/dependency_checker.py

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def check_dependents(
    db: AsyncSession,
    model,
    foreign_key_field: str,
    value,
    entity_name: str,
    only_active: bool = True
):
    """
    Verifica se existem entidades dependentes antes de deletar.
    Lança HTTPException 409 se encontrar dependentes.
    """
    filters = [getattr(model, foreign_key_field) == value]
    if only_active and hasattr(model, "ativo"):
        filters.append(model.ativo == True)

    result = await db.execute(select(model).where(*filters))
    dependent = result.scalars().first()
    if dependent:
        raise HTTPException(
            status_code=409,
            detail=f"Não é possível excluir pois existem {entity_name} vinculados."
        )