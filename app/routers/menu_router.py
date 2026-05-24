from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.menu_schema import MenuResponse
from app.services.menu_service import get_displayed_menus

router = APIRouter(prefix="/menus", tags=["menus"])


@router.get("/", response_model=list[MenuResponse])
async def read_menus(db: Annotated[AsyncSession, Depends(get_db)]):
    return await get_displayed_menus(db)
