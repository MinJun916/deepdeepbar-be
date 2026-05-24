from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.common.pagination_crud import apply_offset_pagination
from app.crud.queries.recipe_query import get_active_recipe_query
from app.models.menu_model import Menu
from app.models.recipe_model import Recipe
from app.schemas.recipe_schema import RecipeFilterData
from app.utils.recipe_filter import apply_recipe_filter


async def find_recipes(db: AsyncSession, filter_data: RecipeFilterData):
    # query = get_active_recipe_query().options(
    #     selectinload(Recipe.menu),
    #     selectinload(Recipe.glass_type),
    #     selectinload(Recipe.steps),
    # )

    query = (
        get_active_recipe_query()
        .join(Menu)
        .options(
            selectinload(Recipe.menu),
            selectinload(Recipe.glass_type),
            selectinload(Recipe.steps),
        )
        .order_by(Menu.name.asc())
    )

    if filter_data.keyword is not None:
        query = apply_recipe_filter(query, filter_data)

    return await apply_offset_pagination(
        db=db,
        query=query,
        offset=filter_data.offset,
        limit=filter_data.limit,
    )
