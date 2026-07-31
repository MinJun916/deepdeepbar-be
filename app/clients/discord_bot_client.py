from __future__ import annotations

import httpx

from app.core.config import settings
from app.models.order_model import Order

DISCORD_API_BASE_URL = "https://discord.com/api/v10"
MAX_DESCRIPTION_LENGTH = 3500
POS_REGISTER_BUTTON_PREFIX = "order_pos_register:"
POS_UNREGISTER_BUTTON_PREFIX = "order_pos_unregister:"


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


def require_bot_configuration() -> tuple[str, str]:
    bot_token = settings.discord_bot_token
    channel_id = settings.discord_order_channel_id

    if bot_token is None or not channel_id:
        raise DiscordBotError(
            "Discord Bot Token 또는 주문 채널 ID가 설정되지 않았습니다."
        )

    return bot_token.get_secret_value(), channel_id


async def send_order_discord_message(order: Order) -> str:
    bot_token, channel_id = require_bot_configuration()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DISCORD_API_BASE_URL}/channels/{channel_id}/messages",
                headers={"Authorization": f"Bot {bot_token}"},
                json=build_order_message_payload(order),
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


async def edit_order_discord_message(
    message_id: str,
    order: Order,
) -> None:
    bot_token, channel_id = require_bot_configuration()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                (f"{DISCORD_API_BASE_URL}/channels/{channel_id}/messages/{message_id}"),
                headers={"Authorization": f"Bot {bot_token}"},
                json=build_order_message_payload(order),
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
