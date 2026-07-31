from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth_dependency import require_admin
from app.models.user_model import User
from app.schemas.store_setting_schema import (
    OrderModeResponse,
    UpdateOrderModeRequest,
)
from app.services.store_setting_service import get_order_mode, update_order_mode

router = APIRouter(prefix="/store-settings", tags=["store-settings"])

db = Annotated[AsyncSession, Depends(get_db)]
authorized_admin = Annotated[User, Depends(require_admin)]


@router.get(
    "/order-mode",
    response_model=OrderModeResponse,
    summary="주문 모드 조회",
    description="프론트엔드에서 메뉴판 전용 또는 주문 가능 모드를 확인합니다.",
)
async def read_order_mode(db: db):
    return await get_order_mode(db)


@router.patch(
    "/order-mode",
    response_model=OrderModeResponse,
    summary="주문 모드 변경",
    description="관리자가 메뉴판 전용 또는 주문 가능 모드로 변경합니다.",
)
async def patch_order_mode(
    order_mode_data: UpdateOrderModeRequest,
    current_user: authorized_admin,
    db: db,
):
    return await update_order_mode(db, order_mode_data.is_order_enabled)
