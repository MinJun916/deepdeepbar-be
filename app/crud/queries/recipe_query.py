from sqlalchemy import select

from app.models.recipe_model import Recipe


def get_active_recipe_query():
    return select(Recipe).where(
        Recipe.deleted_at.is_(None),
    )
