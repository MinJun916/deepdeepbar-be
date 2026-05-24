from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.recipe_crud import find_recipes


async def get_recipes(
    db: AsyncSession,
):
    return await find_recipes(db)
