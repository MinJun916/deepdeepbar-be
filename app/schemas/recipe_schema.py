import uuid

from fastapi import Query
from pydantic import BaseModel

from app.schemas.common_schema import OffsetPaginatedResponse
from app.schemas.glass_type_schema import GlassTypeResponse
from app.schemas.menu_schema import MenuResponseForRecipe
from app.schemas.recipe_step_schema import RecipeStepResponse


class RecipeResponse(BaseModel):
    id: uuid.UUID
    menu_id: uuid.UUID
    glass_type_id: uuid.UUID
    garnish: str | None
    mixing_method: str
    notes: str | None

    menu: MenuResponseForRecipe
    glass_type: GlassTypeResponse
    steps: list[RecipeStepResponse]


RecipeListResponse = OffsetPaginatedResponse[RecipeResponse]


class RecipeFilterData(BaseModel):
    keyword: str | None = None
    offset: int = Query(default=0, ge=0)
    limit: int = Query(default=20, ge=1, le=100)
