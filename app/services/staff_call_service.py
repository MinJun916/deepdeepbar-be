import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.discord_bot_client import (
    DiscordBotError,
    build_staff_call_message_payload,
    create_discord_message,
    require_channel_id,
)
from app.constants.status_code import BAD_REQUEST, NOT_FOUND, UNAUTHORIZED
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import hash_token
from app.crud.order_crud import find_locked_active_table_session_crud
from app.crud.staff_call_crud import require_option
from app.crud.table_session_crud import find_active_table_session_by_token_hash_crud
from app.models.base_model import get_utc_now
from app.models.staff_call_model import StaffCall


async def get_current_calls(db: AsyncSession, token: str):
    session = await find_active_table_session_by_token_hash_crud(db, hash_token(token))
    result = await db.execute(
        select(StaffCall)
        .where(StaffCall.table_session_id == session.id)
        .order_by(StaffCall.created_at)
    )
    return list(result.scalars().all())


async def create_staff_call(db: AsyncSession, token: str, option_id: uuid.UUID):
    session = await find_locked_active_table_session_crud(db, hash_token(token))
    option = await require_option(db, option_id)
    if not option.is_active:
        raise AppError(
            status_code=BAD_REQUEST, message="현재 사용할 수 없는 호출 항목입니다."
        )
    result = await db.execute(
        select(StaffCall)
        .where(
            StaffCall.table_session_id == session.id,
            StaffCall.option_id == option_id,
            StaffCall.completed_at.is_(None),
        )
        .with_for_update()
    )
    call = result.scalar_one_or_none()
    if call is None:
        call = StaffCall(
            table_session_id=session.id,
            table_number=session.table_number,
            option_id=option_id,
            label=option.label,
            notification_status="pending",
        )
        db.add(call)
    now = get_utc_now()
    if not call.retry_available:
        await db.commit()
        return call
    delivery_token = uuid.uuid4()
    call.notification_status = "sending"
    call.last_attempted_at = now
    call.delivery_token = delivery_token
    await db.commit()
    call_id = call.id
    try:
        channel = require_channel_id(settings.discord_order_channel_id, "직원 호출")
        message_id = await create_discord_message(
            channel, build_staff_call_message_payload(call)
        )
    except DiscordBotError:
        message_id = None
    result = await db.execute(
        select(StaffCall)
        .where(StaffCall.id == call_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    call = result.scalar_one()
    if call.delivery_token == delivery_token:
        call.notification_status = "sent" if message_id else "failed"
        call.discord_message_id = message_id
        call.delivery_token = None
        await db.commit()
    return call


async def complete_staff_call(db: AsyncSession, call_id: uuid.UUID, message_id: str):
    result = await db.execute(
        select(StaffCall)
        .where(StaffCall.id == call_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    call = result.scalar_one_or_none()
    if call is None:
        raise AppError(status_code=NOT_FOUND, message="직원 호출을 찾을 수 없습니다.")
    if not message_id or call.discord_message_id != message_id:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="직원 호출 메시지와 버튼 정보가 일치하지 않습니다.",
        )
    if call.completed_at is None:
        call.completed_at = get_utc_now()
    await db.commit()
    return call
