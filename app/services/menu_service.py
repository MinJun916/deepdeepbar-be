from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.menu_model import Menu


async def get_menus(
    db: AsyncSession,
):
    result = await db.execute(
        select(Menu)
        .options(selectinload(Menu.prices))
        .order_by(
            desc(Menu.is_signature),
            Menu.name.asc(),
        ),
    )

    return result.scalars().all()
