import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.menu_crud import (
    create_menu_crud,
    find_displayed_menus_crud,
    soft_delete_menu_crud,
    update_menu_crud,
)
from app.schemas.menu_schema import (
    CreateMenuRequest,
    UpdateMenuRequest,
)

# async def get_displayed_menus_with_offset(
#     db: AsyncSession,
#     filter_data: MenuOffsetFilterData,
# ):
#     return await find_displayed_menus_with_offset(db, filter_data)


async def get_displayed_menus(
    db: AsyncSession,
):
    return await find_displayed_menus_crud(db)


async def create_menu(
    db: AsyncSession,
    menu_data: CreateMenuRequest,
):
    return await create_menu_crud(db, menu_data)


async def update_menu(
    db: AsyncSession,
    menu_id: uuid.UUID,
    menu_data: UpdateMenuRequest,
):
    return await update_menu_crud(db, menu_id, menu_data)


async def soft_delete_menu(
    db: AsyncSession,
    menu_id: uuid.UUID,
):
    return await soft_delete_menu_crud(db, menu_id)
