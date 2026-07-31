import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import INTERNAL_SERVER_ERROR, NOT_FOUND
from app.core.exceptions import AppError
from app.models.base_model import get_utc_now
from app.models.discord_order_notification_model import DiscordNotificationStatus
from app.models.discord_table_session_notification_model import (
    DiscordTableSessionNotification,
)

DELIVERY_STALE_AFTER = timedelta(minutes=1)


def require_notification(
    notification: DiscordTableSessionNotification | None,
) -> DiscordTableSessionNotification:
    if notification is None:
        raise AppError(
            status_code=NOT_FOUND,
            message="Discord 테이블 알림 내역을 찾을 수 없습니다.",
        )

    return notification


async def find_discord_table_session_notification_crud(
    db: AsyncSession,
    table_session_id: uuid.UUID,
) -> DiscordTableSessionNotification:
    result = await db.execute(
        select(DiscordTableSessionNotification).where(
            DiscordTableSessionNotification.table_session_id == table_session_id,
            DiscordTableSessionNotification.deleted_at.is_(None),
        )
    )
    return require_notification(result.scalar_one_or_none())


async def claim_discord_table_session_notification_crud(
    db: AsyncSession,
    table_session_id: uuid.UUID,
) -> tuple[DiscordTableSessionNotification, uuid.UUID | None]:
    result = await db.execute(
        select(DiscordTableSessionNotification)
        .where(
            DiscordTableSessionNotification.table_session_id == table_session_id,
            DiscordTableSessionNotification.deleted_at.is_(None),
        )
        .with_for_update()
    )
    notification = require_notification(result.scalar_one_or_none())
    now = get_utc_now()

    if notification.status == DiscordNotificationStatus.sent:
        await db.commit()
        return notification, None

    is_active_delivery = (
        notification.status == DiscordNotificationStatus.sending
        and notification.last_attempted_at is not None
        and notification.last_attempted_at > now - DELIVERY_STALE_AFTER
    )

    if is_active_delivery:
        await db.commit()
        return notification, None

    delivery_token = uuid.uuid4()
    notification.status = DiscordNotificationStatus.sending
    notification.attempt_count += 1
    notification.last_attempted_at = now
    notification.last_error = None
    notification.delivery_token = delivery_token
    notification.updated_at = now

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return notification, delivery_token


async def complete_discord_table_session_notification_crud(
    db: AsyncSession,
    notification_id: uuid.UUID,
    delivery_token: uuid.UUID,
    *,
    message_id: str | None = None,
    error_message: str | None = None,
) -> DiscordTableSessionNotification:
    result = await db.execute(
        select(DiscordTableSessionNotification)
        .where(
            DiscordTableSessionNotification.id == notification_id,
            DiscordTableSessionNotification.delivery_token == delivery_token,
            DiscordTableSessionNotification.deleted_at.is_(None),
        )
        .with_for_update()
    )
    notification = result.scalar_one_or_none()

    if notification is None:
        raise AppError(
            status_code=INTERNAL_SERVER_ERROR,
            message="Discord 테이블 알림 전송 상태가 이미 변경되었습니다.",
        )

    completed_at = get_utc_now()

    if message_id is not None:
        notification.status = DiscordNotificationStatus.sent
        notification.discord_message_id = message_id
        notification.sent_at = completed_at
        notification.last_error = None
    else:
        notification.status = DiscordNotificationStatus.failed
        notification.last_error = (error_message or "알 수 없는 오류")[:1000]

    notification.delivery_token = None
    notification.updated_at = completed_at

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return notification
