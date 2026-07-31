import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.discord_bot_client import (
    POS_REGISTER_BUTTON_PREFIX,
    POS_UNREGISTER_BUTTON_PREFIX,
    TABLE_CHECKOUT_BUTTON_PREFIX,
    build_order_message_payload,
    build_table_session_message_payload,
)
from app.constants.status_code import (
    BAD_REQUEST,
    INTERNAL_SERVER_ERROR,
    UNAUTHORIZED,
)
from app.core.config import settings
from app.core.exceptions import AppError
from app.services.discord_order_notification_service import (
    get_discord_order_notification,
)
from app.services.discord_table_session_notification_service import (
    get_discord_table_session_notification,
)
from app.services.order_service import update_order_pos_registration
from app.services.table_session_service import checkout_table_session

PING = 1
MESSAGE_COMPONENT = 3
PONG = 1
CHANNEL_MESSAGE_WITH_SOURCE = 4
UPDATE_MESSAGE = 7
EPHEMERAL = 1 << 6


def ephemeral_response(message: str) -> dict:
    return {
        "type": CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {
            "content": message,
            "flags": EPHEMERAL,
        },
    }


def validate_interaction_context(payload: dict) -> None:
    application_id = settings.discord_application_id

    if not application_id:
        raise AppError(
            status_code=INTERNAL_SERVER_ERROR,
            message="Discord Application ID가 설정되지 않았습니다.",
        )

    if payload.get("application_id") != application_id:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="다른 Discord Application의 요청입니다.",
        )


def validate_component_context(payload: dict, expected_channel_id: str | None) -> None:
    guild_id = settings.discord_guild_id

    if not guild_id or not expected_channel_id:
        raise AppError(
            status_code=INTERNAL_SERVER_ERROR,
            message="Discord 서버 또는 대상 채널 ID가 설정되지 않았습니다.",
        )

    if (
        payload.get("guild_id") != guild_id
        or payload.get("channel_id") != expected_channel_id
    ):
        raise AppError(
            status_code=UNAUTHORIZED,
            message="허용되지 않은 Discord 서버 또는 채널입니다.",
        )


def parse_pos_registration_action(custom_id: str) -> tuple[uuid.UUID, bool]:
    action_prefixes = {
        POS_REGISTER_BUTTON_PREFIX: True,
        POS_UNREGISTER_BUTTON_PREFIX: False,
    }
    matched_action = next(
        (
            (prefix, is_registered)
            for prefix, is_registered in action_prefixes.items()
            if custom_id.startswith(prefix)
        ),
        None,
    )

    if matched_action is None:
        raise AppError(
            status_code=BAD_REQUEST,
            message="지원하지 않는 Discord 버튼입니다.",
        )

    prefix, is_registered = matched_action

    try:
        order_id = uuid.UUID(custom_id.removeprefix(prefix))
    except ValueError:
        raise AppError(
            status_code=BAD_REQUEST,
            message="Discord 버튼의 주문 ID가 올바르지 않습니다.",
        ) from None

    return order_id, is_registered


def parse_table_checkout_action(custom_id: str) -> uuid.UUID:
    if not custom_id.startswith(TABLE_CHECKOUT_BUTTON_PREFIX):
        raise AppError(
            status_code=BAD_REQUEST,
            message="지원하지 않는 Discord 버튼입니다.",
        )

    try:
        return uuid.UUID(custom_id.removeprefix(TABLE_CHECKOUT_BUTTON_PREFIX))
    except ValueError:
        raise AppError(
            status_code=BAD_REQUEST,
            message="Discord 버튼의 테이블 세션 ID가 올바르지 않습니다.",
        ) from None


def get_discord_user_id(payload: dict) -> str:
    user_id = payload.get("member", {}).get("user", {}).get("id") or payload.get(
        "user", {}
    ).get("id")

    if not user_id:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="Discord 처리자 정보를 확인할 수 없습니다.",
        )

    return str(user_id)


async def handle_order_component(
    db: AsyncSession,
    payload: dict,
    custom_id: str,
) -> dict:
    validate_component_context(payload, settings.discord_order_channel_id)
    order_id, is_registered = parse_pos_registration_action(custom_id)
    notification = await get_discord_order_notification(db, order_id)
    message_id = payload.get("message", {}).get("id")

    if notification.discord_message_id != message_id:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="주문 알림 메시지와 버튼 정보가 일치하지 않습니다.",
        )

    order = await update_order_pos_registration(
        db,
        order_id,
        is_registered,
        sync_discord_message=False,
    )
    return {"type": UPDATE_MESSAGE, "data": build_order_message_payload(order)}


async def handle_table_checkout_component(
    db: AsyncSession,
    payload: dict,
    custom_id: str,
) -> dict:
    validate_component_context(payload, settings.discord_table_channel_id)
    table_session_id = parse_table_checkout_action(custom_id)
    notification = await get_discord_table_session_notification(
        db,
        table_session_id,
    )
    message_id = payload.get("message", {}).get("id")

    if notification.discord_message_id != message_id:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="테이블 알림 메시지와 버튼 정보가 일치하지 않습니다.",
        )

    table_session = await checkout_table_session(
        db,
        table_session_id,
        checked_out_by_discord_user_id=get_discord_user_id(payload),
        sync_discord_message=False,
    )
    return {
        "type": UPDATE_MESSAGE,
        "data": build_table_session_message_payload(table_session),
    }


async def handle_discord_interaction(
    db: AsyncSession,
    payload: dict,
) -> dict:
    validate_interaction_context(payload)
    interaction_type = payload.get("type")

    if interaction_type == PING:
        return {"type": PONG}

    if interaction_type != MESSAGE_COMPONENT:
        return ephemeral_response("지원하지 않는 Discord 기능입니다.")

    try:
        custom_id = payload.get("data", {}).get("custom_id", "")
        if custom_id.startswith(TABLE_CHECKOUT_BUTTON_PREFIX):
            return await handle_table_checkout_component(db, payload, custom_id)

        return await handle_order_component(db, payload, custom_id)
    except AppError as error:
        return ephemeral_response(error.message)
