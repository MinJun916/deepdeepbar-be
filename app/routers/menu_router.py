from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth_dependency import require_admin
from app.models.user_model import User
from app.schemas.menu_schema import (
    CreateMenuRequest,
    MenuOffsetFilterData,
    MenuOffsetResponse,
    MenuResponse,
)
from app.services.menu_service import (
    create_menu,
    get_displayed_menus_with_offset,
)

router = APIRouter(prefix="/menus", tags=["menus"])


@router.get("/", response_model=MenuOffsetResponse)
async def read_menus_with_offset(
    db: Annotated[AsyncSession, Depends(get_db)],
    filter_data: Annotated[MenuOffsetFilterData, Depends()],
):
    return await get_displayed_menus_with_offset(db, filter_data)


@router.post("/", response_model=MenuResponse)
async def add_menu(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    menu_data: CreateMenuRequest,
):
    return await create_menu(db, menu_data)
