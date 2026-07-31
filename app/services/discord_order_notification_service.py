import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.discord_webhook_client import (
    DiscordWebhookError,
    send_order_webhook,
)
from app.constants.status_code import BAD_GATEWAY, NOT_FOUND
from app.core.exceptions import AppError
from app.core.logger import logger
from app.crud.discord_order_notification_crud import (
    claim_discord_order_notification_crud,
    complete_discord_order_notification_crud,
    find_discord_order_notification_crud,
)
from app.crud.order_crud import find_order_by_id_crud
from app.models.discord_order_notification_model import DiscordOrderNotification


async def get_discord_order_notification(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> DiscordOrderNotification:
    return await find_discord_order_notification_crud(db, order_id)


async def dispatch_discord_order_notification(
    db: AsyncSession,
    order_id: uuid.UUID,
    *,
    raise_on_failure: bool = False,
) -> DiscordOrderNotification:
    order = await find_order_by_id_crud(db, order_id)

    if order is None or order.deleted_at is not None:
        raise AppError(
            status_code=NOT_FOUND,
            message="주문을 찾을 수 없습니다.",
        )

    notification, delivery_token = await claim_discord_order_notification_crud(
        db, order_id
    )

    if delivery_token is None:
        return notification

    try:
        message_id = await send_order_webhook(order)
    except DiscordWebhookError as error:
        failed_notification = await complete_discord_order_notification_crud(
            db,
            notification.id,
            delivery_token,
            error_message=str(error),
        )
        logger.warning(
            "discord_order_notification_failed",
            order_id=str(order_id),
            attempt_count=failed_notification.attempt_count,
            error=str(error),
        )

        if raise_on_failure:
            raise AppError(
                status_code=BAD_GATEWAY,
                message=str(error),
            ) from error

        return failed_notification

    sent_notification = await complete_discord_order_notification_crud(
        db,
        notification.id,
        delivery_token,
        message_id=message_id,
    )
    logger.info(
        "discord_order_notification_sent",
        order_id=str(order_id),
        attempt_count=sent_notification.attempt_count,
    )
    return sent_notification


async def retry_discord_order_notification(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> DiscordOrderNotification:
    return await dispatch_discord_order_notification(
        db,
        order_id,
        raise_on_failure=True,
    )


async def try_dispatch_discord_order_notification(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> None:
    try:
        await dispatch_discord_order_notification(db, order_id)
    except Exception:
        logger.exception(
            "discord_order_notification_unexpected_error",
            order_id=str(order_id),
        )
