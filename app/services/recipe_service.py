from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.recipe_model import Recipe


async def get_recipes(
    db: AsyncSession,
):
    result = await db.execute(
        select(Recipe).options(
            selectinload(Recipe.menu),
            selectinload(Recipe.glass_type),
            selectinload(Recipe.steps),
        )
    )

    return result.scalars().all()
