from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.queries.menu_query import get_displayed_menu_query
from app.models.menu_model import Menu


async def find_displayed_menus(db: AsyncSession) -> list[Menu]:
    query = (
        get_displayed_menu_query()
        .options(selectinload(Menu.prices))
        .order_by(Menu.is_signature, Menu.name)
    )

    return await db.execute(query)
