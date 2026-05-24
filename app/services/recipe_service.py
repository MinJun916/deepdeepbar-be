from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.recipe_crud import create_recipe_crud, find_recipes
from app.schemas.recipe_schema import CreateRecipeRequest, RecipeFilterData


async def get_recipes(
    db: AsyncSession,
    filter_data: RecipeFilterData,
):
    return await find_recipes(db, filter_data)


async def create_recipe(
    db: AsyncSession,
    recipe_data: CreateRecipeRequest,
):
    return await create_recipe_crud(db, recipe_data)
