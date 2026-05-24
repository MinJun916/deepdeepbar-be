from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.menu_crud import create_menu_crud, find_displayed_menus_with_offset
from app.schemas.menu_schema import CreateMenuRequest, MenuOffsetFilterData


async def get_displayed_menus_with_offset(
    db: AsyncSession,
    filter_data: MenuOffsetFilterData,
):
    return await find_displayed_menus_with_offset(db, filter_data)


async def create_menu(
    db: AsyncSession,
    menu_data: CreateMenuRequest,
):
    return await create_menu_crud(db, menu_data)
