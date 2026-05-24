import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants.status_code import INTERNAL_SERVER_ERROR, NOT_FOUND
from app.core.exceptions import AppError
from app.crud.common.pagination_crud import apply_offset_pagination
from app.crud.glass_type_crud import find_glass_type_id_by_code_crud
from app.crud.queries.recipe_query import get_active_recipe_query
from app.models.menu_model import Menu
from app.models.recipe_model import Recipe
from app.models.recipe_step_model import RecipeStep
from app.schemas.recipe_schema import (
    CreateRecipeRequest,
    RecipeFilterData,
    UpdateRecipeRequest,
)
from app.utils.recipe_filter import apply_recipe_filter


async def find_recipe_by_id_crud(db: AsyncSession, recipe_id: uuid.UUID):
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    return result.scalar_one_or_none()


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


async def find_recipe_by_id_with_relations_crud(db: AsyncSession, recipe_id: uuid.UUID):
    result = await db.execute(
        select(Recipe)
        .options(
            selectinload(Recipe.menu),
            selectinload(Recipe.glass_type),
            selectinload(Recipe.steps),
        )
        .where(Recipe.id == recipe_id)
    )
    return result.scalar_one_or_none()


async def create_recipe_crud(db: AsyncSession, recipe_data: CreateRecipeRequest):
    try:
        glass_type_id = await find_glass_type_id_by_code_crud(
            db, recipe_data.glass_type
        )

        if glass_type_id is None:
            raise AppError(status_code=NOT_FOUND, message="Glass type not found")

        recipe = Recipe(
            menu_id=recipe_data.menu_id,
            glass_type_id=glass_type_id,
            garnish=recipe_data.garnish,
            mixing_method=recipe_data.mixing_method,
            notes=recipe_data.notes,
        )

        db.add(recipe)

        await db.flush()

        steps = [
            RecipeStep(
                recipe_id=recipe.id,
                step_order=step_data.step_order,
                instruction=step_data.instruction,
            )
            for step_data in recipe_data.steps
        ]

        db.add_all(steps)

        await db.commit()

        return await find_recipe_by_id_with_relations_crud(db, recipe.id)

    except Exception as error:
        await db.rollback()
        raise AppError(status_code=INTERNAL_SERVER_ERROR, message=str(error))


async def update_recipe_crud(
    db: AsyncSession, recipe_id: uuid.UUID, recipe_data: UpdateRecipeRequest
):
    try:
        recipe = await find_recipe_by_id_with_relations_crud(db, recipe_id)

        if recipe is None:
            raise AppError(status_code=NOT_FOUND, message="Recipe not found")

        if recipe_data.glass_type is not None:
            glass_type_id = await find_glass_type_id_by_code_crud(
                db, recipe_data.glass_type
            )

            if glass_type_id is None:
                raise AppError(status_code=NOT_FOUND, message="Glass type not found")

            recipe.glass_type_id = glass_type_id

        update_data = recipe_data.model_dump(
            exclude_unset=True,
            exclude={"glass_type", "steps"},
        )

        for key, value in update_data.items():
            setattr(recipe, key, value)

        if recipe_data.steps is not None:
            for step in recipe.steps:
                await db.delete(step)

            await db.flush()

            steps = [
                RecipeStep(
                    recipe_id=recipe.id,
                    step_order=step_data.step_order,
                    instruction=step_data.instruction,
                )
                for step_data in recipe_data.steps
            ]

            db.add_all(steps)

        await db.commit()
        db.expire(recipe, ["steps"])

        return await find_recipe_by_id_with_relations_crud(db, recipe.id)

    except AppError:
        await db.rollback()
        raise

    except Exception as error:
        await db.rollback()
        raise AppError(status_code=INTERNAL_SERVER_ERROR, message=str(error))


async def soft_delete_recipe_crud(db: AsyncSession, recipe_id: uuid.UUID):
    recipe = await find_recipe_by_id_crud(db, recipe_id)

    if recipe is None:
        raise AppError(status_code=NOT_FOUND, message="Recipe not found")

    recipe.deleted_at = datetime.now()

    await db.commit()
    await db.refresh(recipe)

    return {
        "id": recipe.id,
        "deleted_at": recipe.deleted_at,
        "message": "Recipe deleted successfully",
    }
