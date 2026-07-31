import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.discord_bot_client import (
    DiscordBotError,
    edit_table_session_discord_message,
    send_table_session_discord_message,
)
from app.constants.status_code import BAD_GATEWAY, NOT_FOUND
from app.core.exceptions import AppError
from app.core.logger import logger
from app.crud.discord_table_session_notification_crud import (
    claim_discord_table_session_notification_crud,
    complete_discord_table_session_notification_crud,
    find_discord_table_session_notification_crud,
)
from app.crud.table_session_crud import find_table_session_by_id_crud
from app.models.discord_table_session_notification_model import (
    DiscordTableSessionNotification,
)
from app.models.table_session_model import TableSession


async def get_discord_table_session_notification(
    db: AsyncSession,
    table_session_id: uuid.UUID,
) -> DiscordTableSessionNotification:
    return await find_discord_table_session_notification_crud(db, table_session_id)


async def dispatch_discord_table_session_notification(
    db: AsyncSession,
    table_session_id: uuid.UUID,
    *,
    raise_on_failure: bool = False,
) -> DiscordTableSessionNotification:
    table_session = await find_table_session_by_id_crud(db, table_session_id)

    if table_session is None or table_session.deleted_at is not None:
        raise AppError(
            status_code=NOT_FOUND,
            message="테이블 세션을 찾을 수 없습니다.",
        )

    notification, delivery_token = await claim_discord_table_session_notification_crud(
        db, table_session_id
    )

    if delivery_token is None:
        return notification

    try:
        message_id = await send_table_session_discord_message(table_session)
    except DiscordBotError as error:
        failed_notification = await complete_discord_table_session_notification_crud(
            db,
            notification.id,
            delivery_token,
            error_message=str(error),
        )
        logger.warning(
            "discord_table_session_notification_failed",
            table_session_id=str(table_session_id),
            attempt_count=failed_notification.attempt_count,
            error=str(error),
        )

        if raise_on_failure:
            raise AppError(status_code=BAD_GATEWAY, message=str(error)) from error

        return failed_notification

    sent_notification = await complete_discord_table_session_notification_crud(
        db,
        notification.id,
        delivery_token,
        message_id=message_id,
    )
    logger.info(
        "discord_table_session_notification_sent",
        table_session_id=str(table_session_id),
        attempt_count=sent_notification.attempt_count,
    )
    return sent_notification


async def retry_discord_table_session_notification(
    db: AsyncSession,
    table_session_id: uuid.UUID,
) -> DiscordTableSessionNotification:
    return await dispatch_discord_table_session_notification(
        db,
        table_session_id,
        raise_on_failure=True,
    )


async def try_dispatch_discord_table_session_notification(
    db: AsyncSession,
    table_session_id: uuid.UUID,
) -> None:
    try:
        await dispatch_discord_table_session_notification(db, table_session_id)
    except Exception:
        logger.exception(
            "discord_table_session_notification_unexpected_error",
            table_session_id=str(table_session_id),
        )


async def sync_discord_table_session_message(
    db: AsyncSession,
    table_session: TableSession,
) -> None:
    notification = await find_discord_table_session_notification_crud(
        db,
        table_session.id,
    )

    if not notification.discord_message_id:
        return

    await edit_table_session_discord_message(
        notification.discord_message_id,
        table_session,
    )
    logger.info(
        "discord_table_session_message_synced",
        table_session_id=str(table_session.id),
    )


async def try_sync_discord_table_session_message(
    db: AsyncSession,
    table_session: TableSession,
) -> None:
    try:
        await sync_discord_table_session_message(db, table_session)
    except AppError as error:
        if error.status_code == NOT_FOUND:
            return
        logger.exception(
            "discord_table_session_message_sync_failed",
            table_session_id=str(table_session.id),
        )
    except Exception:
        logger.exception(
            "discord_table_session_message_sync_failed",
            table_session_id=str(table_session.id),
        )
