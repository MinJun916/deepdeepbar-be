import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import NOT_FOUND
from app.core.exceptions import AppError
from app.models.base_model import get_utc_now
from app.models.staff_call_model import StaffCallOption
from app.schemas.staff_call_schema import StaffCallOptionRequest


async def get_options(db: AsyncSession, *, admin: bool = False):
    query = select(StaffCallOption).where(StaffCallOption.deleted_at.is_(None))
    if not admin:
        query = query.where(StaffCallOption.is_active.is_(True))
    result = await db.execute(
        query.order_by(StaffCallOption.display_order, StaffCallOption.created_at)
    )
    return list(result.scalars().all())


async def require_option(db: AsyncSession, option_id: uuid.UUID):
    option = await db.get(StaffCallOption, option_id)
    if option is None or option.deleted_at is not None:
        raise AppError(
            status_code=NOT_FOUND, message="직원 호출 항목을 찾을 수 없습니다."
        )
    return option


async def save_option(
    db: AsyncSession, data: StaffCallOptionRequest, option_id: uuid.UUID | None = None
):
    option = await require_option(db, option_id) if option_id else StaffCallOption()
    for key, value in data.model_dump().items():
        setattr(option, key, value)
    db.add(option)
    await db.commit()
    await db.refresh(option)
    return option


async def delete_option(db: AsyncSession, option_id: uuid.UUID):
    option = await require_option(db, option_id)
    option.deleted_at = get_utc_now()
    option.is_active = False
    await db.commit()
