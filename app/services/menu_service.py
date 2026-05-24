from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.menu_crud import find_displayed_menus


async def get_displayed_menus(
    db: AsyncSession,
):
    return await find_displayed_menus(db)
