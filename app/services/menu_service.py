from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.menu_crud import find_menus


async def get_menus(
    db: AsyncSession,
):
    return await find_menus(db)
