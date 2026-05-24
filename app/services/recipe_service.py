from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.recipe_crud import find_recipes
from app.schemas.recipe_schema import RecipeFilterData


async def get_recipes(
    db: AsyncSession,
    filter_data: RecipeFilterData | None = None,
):
    return await find_recipes(db, filter_data)
