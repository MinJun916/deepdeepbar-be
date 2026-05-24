from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.menu_model import Menu


async def find_menus(db: AsyncSession) -> list[Menu]:
    result = await db.execute(
        select(Menu)
        .options(selectinload(Menu.prices))
        .order_by(Menu.is_signature, Menu.name)
    )

    return result.scalars().all()
