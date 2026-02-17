from fastapi import HTTPException
from models import ORM_CLS, ORM_OBJ, Advertisement
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

async def add_item(session: AsyncSession, item: ORM_OBJ):
    session.add(item)
    try:
        await session.commit()
        await session.refresh(item)  # Обновляем объект, чтобы получить, например, автоматический ID
        return item
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "Integrity error: possible violation of unique constraint")

async def update_existing_item(session: AsyncSession, item: ORM_OBJ, update_data: dict):
    for field, value in update_data.items():
        setattr(item, field, value)
    try:
        await session.commit()
        return item
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "Conflict while updating item")

async def get_item_by_id(
    session: AsyncSession, orm_cls: ORM_CLS, item_id: int
) -> ORM_OBJ:
    orm_obj = await session.get(orm_cls, item_id)
    if orm_obj is None:
        raise HTTPException(404, f"Item not found")
    return orm_obj


async def delete_item(session: AsyncSession, item: ORM_OBJ):
    await session.delete(item)
    await session.commit()