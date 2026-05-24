from sqlalchemy import or_

from app.models.menu_model import Menu
from app.schemas.recipe_schema import RecipeFilterData


def create_keyword_condition(column, keyword: str):
    return column.ilike(f"%{keyword}%")


def apply_recipe_filter(query, filter_data: RecipeFilterData):

    filters = []

    if filter_data.keyword is not None:
        filters.append(
            or_(
                create_keyword_condition(Menu.name, filter_data.keyword),
                create_keyword_condition(Menu.name_en, filter_data.keyword),
            )
        )

    if filters:
        query = query.where(*filters)

    return query
