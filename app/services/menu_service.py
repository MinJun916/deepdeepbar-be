from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.menu_crud import find_displayed_menus_with_offset
from app.schemas.menu_schema import MenuOffsetFilterData


async def get_displayed_menus_with_offset(
    db: AsyncSession,
    filter_data: MenuOffsetFilterData,
):
    return await find_displayed_menus_with_offset(db, filter_data)
