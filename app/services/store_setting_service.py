from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import CONFLICT
from app.core.exceptions import AppError
from app.crud.store_setting_crud import (
    find_store_setting_crud,
    find_store_setting_for_order_crud,
    update_order_mode_crud,
)
from app.models.store_setting_model import StoreSetting


async def get_order_mode(db: AsyncSession) -> StoreSetting:
    return await find_store_setting_crud(db)


async def ensure_ordering_enabled(db: AsyncSession) -> None:
    setting = await find_store_setting_for_order_crud(db)

    if not setting.is_order_enabled:
        await db.rollback()
        raise AppError(
            status_code=CONFLICT,
            message="현재 메뉴판 전용 모드로 주문할 수 없습니다.",
        )


async def update_order_mode(
    db: AsyncSession,
    is_order_enabled: bool,
) -> StoreSetting:
    return await update_order_mode_crud(db, is_order_enabled)
