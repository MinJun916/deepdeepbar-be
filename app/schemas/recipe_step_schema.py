import uuid

from pydantic import BaseModel


class RecipeStepResponse(BaseModel):
    id: uuid.UUID
    recipe_id: uuid.UUID
    step_order: int
    instruction: str


class CreateAndUpdateRecipeStepRequest(BaseModel):
    step_order: int
    instruction: str
