import uuid

from pydantic import BaseModel

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


class RecipeFilterData(BaseModel):
    keyword: str | None = None
