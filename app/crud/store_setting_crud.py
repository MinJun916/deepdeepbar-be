from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import INTERNAL_SERVER_ERROR
from app.core.exceptions import AppError
from app.models.base_model import get_utc_now
from app.models.store_setting_model import GLOBAL_STORE_SCOPE, StoreSetting


def require_store_setting(setting: StoreSetting | None) -> StoreSetting:
    if setting is None:
        raise AppError(
            status_code=INTERNAL_SERVER_ERROR,
            message="매장 운영 설정을 찾을 수 없습니다.",
        )

    return setting


async def find_store_setting_crud(db: AsyncSession) -> StoreSetting:
    result = await db.execute(
        select(StoreSetting).where(
            StoreSetting.scope == GLOBAL_STORE_SCOPE,
            StoreSetting.deleted_at.is_(None),
        )
    )
    return require_store_setting(result.scalar_one_or_none())


async def find_store_setting_for_order_crud(db: AsyncSession) -> StoreSetting:
    result = await db.execute(
        select(StoreSetting)
        .where(
            StoreSetting.scope == GLOBAL_STORE_SCOPE,
            StoreSetting.deleted_at.is_(None),
        )
        .with_for_update(read=True)
    )
    return require_store_setting(result.scalar_one_or_none())


async def update_order_mode_crud(
    db: AsyncSession,
    is_order_enabled: bool,
) -> StoreSetting:
    result = await db.execute(
        select(StoreSetting)
        .where(
            StoreSetting.scope == GLOBAL_STORE_SCOPE,
            StoreSetting.deleted_at.is_(None),
        )
        .with_for_update()
    )
    setting = require_store_setting(result.scalar_one_or_none())

    if setting.is_order_enabled == is_order_enabled:
        await db.commit()
        return setting

    setting.is_order_enabled = is_order_enabled
    setting.updated_at = get_utc_now()

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return setting
