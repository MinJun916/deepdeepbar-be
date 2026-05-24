from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.common.pagination_crud import apply_offset_pagination
from app.crud.queries.menu_query import get_displayed_menu_query
from app.models.menu_model import Menu
from app.schemas.menu_schema import MenuOffsetFilterData

MENU_ORDER_BY = (
    desc(Menu.is_signature),
    Menu.name.asc(),
)


async def find_displayed_menus_with_offset(
    db: AsyncSession,
    filter_data: MenuOffsetFilterData,
):
    query = (
        get_displayed_menu_query()
        .options(selectinload(Menu.prices))
        .order_by(*MENU_ORDER_BY)
    )

    return await apply_offset_pagination(
        db=db,
        query=query,
        offset=filter_data.offset,
        limit=filter_data.limit,
    )
