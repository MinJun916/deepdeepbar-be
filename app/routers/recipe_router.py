import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth_dependency import require_staff_or_admin
from app.models.user_model import User
from app.schemas.recipe_schema import (
    CreateRecipeRequest,
    RecipeFilterData,
    RecipeListResponse,
    RecipeResponse,
    UpdateRecipeRequest,
)
from app.services.recipe_service import create_recipe, get_recipes, update_recipe

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/", response_model=RecipeListResponse)
async def read_recipes(
    current_user: Annotated[User, Depends(require_staff_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    filter_data: Annotated[RecipeFilterData, Depends()],
):
    return await get_recipes(db, filter_data)


@router.post("/", response_model=RecipeResponse)
async def add_recipe(
    current_user: Annotated[User, Depends(require_staff_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    recipe_data: CreateRecipeRequest,
):
    return await create_recipe(db, recipe_data)


@router.patch("/{recipe_id}", response_model=RecipeResponse)
async def patch_recipe(
    current_user: Annotated[User, Depends(require_staff_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    recipe_id: uuid.UUID,
    recipe_data: UpdateRecipeRequest,
):
    return await update_recipe(db, recipe_id, recipe_data)
