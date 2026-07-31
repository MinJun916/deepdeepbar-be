import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import INTERNAL_SERVER_ERROR, NOT_FOUND
from app.core.exceptions import AppError
from app.models.base_model import get_utc_now
from app.models.discord_order_notification_model import (
    DiscordNotificationStatus,
    DiscordOrderNotification,
)

DELIVERY_STALE_AFTER = timedelta(minutes=1)


def require_notification(
    notification: DiscordOrderNotification | None,
) -> DiscordOrderNotification:
    if notification is None:
        raise AppError(
            status_code=NOT_FOUND,
            message="Discord 주문 알림 내역을 찾을 수 없습니다.",
        )

    return notification


async def find_discord_order_notification_crud(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> DiscordOrderNotification:
    result = await db.execute(
        select(DiscordOrderNotification).where(
            DiscordOrderNotification.order_id == order_id,
            DiscordOrderNotification.deleted_at.is_(None),
        )
    )
    return require_notification(result.scalar_one_or_none())


async def claim_discord_order_notification_crud(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> tuple[DiscordOrderNotification, uuid.UUID | None]:
    result = await db.execute(
        select(DiscordOrderNotification)
        .where(
            DiscordOrderNotification.order_id == order_id,
            DiscordOrderNotification.deleted_at.is_(None),
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


async def complete_discord_order_notification_crud(
    db: AsyncSession,
    notification_id: uuid.UUID,
    delivery_token: uuid.UUID,
    *,
    message_id: str | None = None,
    error_message: str | None = None,
) -> DiscordOrderNotification:
    result = await db.execute(
        select(DiscordOrderNotification)
        .where(
            DiscordOrderNotification.id == notification_id,
            DiscordOrderNotification.delivery_token == delivery_token,
            DiscordOrderNotification.deleted_at.is_(None),
        )
        .with_for_update()
    )
    notification = result.scalar_one_or_none()

    if notification is None:
        raise AppError(
            status_code=INTERNAL_SERVER_ERROR,
            message="Discord 주문 알림 전송 상태가 이미 변경되었습니다.",
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
