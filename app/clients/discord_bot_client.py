from __future__ import annotations

import httpx

from app.core.config import settings
from app.models.order_model import Order
from app.models.table_session_model import TableSession

DISCORD_API_BASE_URL = "https://discord.com/api/v10"
MAX_DESCRIPTION_LENGTH = 3500
POS_REGISTER_BUTTON_PREFIX = "order_pos_register:"
POS_UNREGISTER_BUTTON_PREFIX = "order_pos_unregister:"
TABLE_CHECKOUT_BUTTON_PREFIX = "table_checkout:"


class DiscordBotError(Exception):
    pass


def truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[: max_length - 1]}…"


def build_order_description(order: Order) -> str:
    lines: list[str] = []

    for index, item in enumerate(order.items, start=1):
        menu_name = truncate(item.menu_name, 80)
        line = (
            f"**{index}. {menu_name}** (`{item.price_type}`) "
            f"× {item.quantity} — {item.line_total:,}원"
        )

        if len("\n".join([*lines, line])) > MAX_DESCRIPTION_LENGTH:
            omitted_count = len(order.items) - len(lines)
            lines.append(f"…외 {omitted_count}개 항목")
            break

        lines.append(line)

    return "\n".join(lines)


def build_order_message_payload(order: Order) -> dict:
    is_registered = order.is_pos_registered
    return {
        "allowed_mentions": {"parse": []},
        "embeds": [
            {
                "title": f"🔔 테이블 {order.table_number} 새 주문",
                "description": build_order_description(order),
                "color": 0x2ECC71 if not is_registered else 0x3498DB,
                "fields": [
                    {
                        "name": "총 주문 금액",
                        "value": f"**{order.total_amount:,}원**",
                        "inline": True,
                    },
                    {
                        "name": "포스 등록",
                        "value": "✅ 등록 완료" if is_registered else "⏳ 미등록",
                        "inline": True,
                    },
                    {
                        "name": "주문 ID",
                        "value": f"`{order.id}`",
                        "inline": False,
                    },
                ],
                "timestamp": order.created_at.isoformat(),
            }
        ],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 3,
                        "custom_id": f"{POS_REGISTER_BUTTON_PREFIX}{order.id}",
                        "label": "포스 등록 완료",
                        "emoji": {"name": "✅"},
                        "disabled": is_registered,
                    },
                    {
                        "type": 2,
                        "style": 4,
                        "custom_id": f"{POS_UNREGISTER_BUTTON_PREFIX}{order.id}",
                        "label": "포스 등록 취소",
                        "emoji": {"name": "↩️"},
                        "disabled": not is_registered,
                    },
                ],
            }
        ],
    }


def require_bot_token() -> str:
    bot_token = settings.discord_bot_token

    if bot_token is None:
        raise DiscordBotError("Discord Bot Token이 설정되지 않았습니다.")

    return bot_token.get_secret_value()


def require_channel_id(channel_id: str | None, channel_name: str) -> str:
    if not channel_id:
        raise DiscordBotError(f"Discord {channel_name} 채널 ID가 설정되지 않았습니다.")

    return channel_id


async def create_discord_message(channel_id: str, payload: dict) -> str:
    bot_token = require_bot_token()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DISCORD_API_BASE_URL}/channels/{channel_id}/messages",
                headers={"Authorization": f"Bot {bot_token}"},
                json=payload,
                timeout=settings.discord_timeout_seconds,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise DiscordBotError(
            f"Discord가 HTTP {error.response.status_code} 오류를 반환했습니다."
        ) from error
    except httpx.RequestError as error:
        raise DiscordBotError("Discord 연결에 실패했습니다.") from error
    except httpx.HTTPError as error:
        raise DiscordBotError("Discord 요청 처리 중 오류가 발생했습니다.") from error

    try:
        message_id = response.json()["id"]
    except (KeyError, TypeError, ValueError) as error:
        raise DiscordBotError(
            "Discord 응답에서 메시지 ID를 확인할 수 없습니다."
        ) from error

    return str(message_id)


async def update_discord_message(
    channel_id: str,
    message_id: str,
    payload: dict,
) -> None:
    bot_token = require_bot_token()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{DISCORD_API_BASE_URL}/channels/{channel_id}/messages/{message_id}",
                headers={"Authorization": f"Bot {bot_token}"},
                json=payload,
                timeout=settings.discord_timeout_seconds,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise DiscordBotError(
            f"Discord가 HTTP {error.response.status_code} 오류를 반환했습니다."
        ) from error
    except httpx.RequestError as error:
        raise DiscordBotError("Discord 연결에 실패했습니다.") from error
    except httpx.HTTPError as error:
        raise DiscordBotError("Discord 요청 처리 중 오류가 발생했습니다.") from error


async def send_order_discord_message(order: Order) -> str:
    channel_id = require_channel_id(settings.discord_order_channel_id, "주문")
    return await create_discord_message(
        channel_id,
        build_order_message_payload(order),
    )


async def edit_order_discord_message(
    message_id: str,
    order: Order,
) -> None:
    channel_id = require_channel_id(settings.discord_order_channel_id, "주문")
    await update_discord_message(
        channel_id,
        message_id,
        build_order_message_payload(order),
    )


def build_table_session_message_payload(table_session: TableSession) -> dict:
    is_active = table_session.is_active
    fields = [
        {
            "name": "상태",
            "value": "🟢 이용 중" if is_active else "⚪ 체크아웃 완료",
            "inline": True,
        },
        {
            "name": "체크인 시각",
            "value": f"<t:{int(table_session.created_at.timestamp())}:F>",
            "inline": False,
        },
        {
            "name": "테이블 세션 ID",
            "value": f"`{table_session.id}`",
            "inline": False,
        },
    ]

    if table_session.checked_out_at is not None:
        fields.insert(
            2,
            {
                "name": "체크아웃 시각",
                "value": f"<t:{int(table_session.checked_out_at.timestamp())}:F>",
                "inline": False,
            },
        )
        checkout_actor = (
            f"<@{table_session.checked_out_by_discord_user_id}>"
            if table_session.checked_out_by_discord_user_id
            else "관리자 API"
        )
        fields.insert(
            3,
            {
                "name": "처리자",
                "value": checkout_actor,
                "inline": True,
            },
        )

    return {
        "allowed_mentions": {"parse": []},
        "embeds": [
            {
                "title": (
                    f"🪑 테이블 {table_session.table_number} 체크인"
                    if is_active
                    else f"✅ 테이블 {table_session.table_number} 체크아웃"
                ),
                "color": 0x2ECC71 if is_active else 0x95A5A6,
                "fields": fields,
                "footer": (
                    {"text": "포스 결제 완료 후 체크아웃 버튼을 눌러주세요."}
                    if is_active
                    else {"text": "체크아웃 처리가 완료되었습니다."}
                ),
                "timestamp": table_session.created_at.isoformat(),
            }
        ],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 4,
                        "custom_id": (
                            f"{TABLE_CHECKOUT_BUTTON_PREFIX}{table_session.id}"
                        ),
                        "label": "결제 완료 · 체크아웃",
                        "emoji": {"name": "🚪"},
                        "disabled": not is_active,
                    }
                ],
            }
        ],
    }


async def send_table_session_discord_message(table_session: TableSession) -> str:
    channel_id = require_channel_id(settings.discord_table_channel_id, "테이블")
    return await create_discord_message(
        channel_id,
        build_table_session_message_payload(table_session),
    )


async def edit_table_session_discord_message(
    message_id: str,
    table_session: TableSession,
) -> None:
    channel_id = require_channel_id(settings.discord_table_channel_id, "테이블")
    await update_discord_message(
        channel_id,
        message_id,
        build_table_session_message_payload(table_session),
    )
