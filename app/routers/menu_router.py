from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.menu_schema import (
    MenuOffsetFilterData,
    MenuOffsetResponse,
)
from app.services.menu_service import (
    get_displayed_menus_with_offset,
)

router = APIRouter(prefix="/menus", tags=["menus"])


@router.get("/", response_model=MenuOffsetResponse)
async def read_menus_with_offset(
    db: Annotated[AsyncSession, Depends(get_db)],
    filter_data: Annotated[MenuOffsetFilterData, Depends()],
):
    return await get_displayed_menus_with_offset(db, filter_data)
