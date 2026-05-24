from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth_dependency import require_staff_or_admin
from app.models.user_model import User
from app.schemas.recipe_schema import RecipeFilterData, RecipeResponse
from app.services.recipe_service import get_recipes

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/", response_model=list[RecipeResponse])
async def read_recipes(
    current_user: Annotated[User, Depends(require_staff_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    filter_data: Annotated[RecipeFilterData, Depends()],
):
    return await get_recipes(db, filter_data)
