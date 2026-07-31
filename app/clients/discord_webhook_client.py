from __future__ import annotations

import httpx

from app.core.config import settings
from app.models.order_model import Order

MAX_DESCRIPTION_LENGTH = 3500


class DiscordWebhookError(Exception):
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


def build_order_webhook_payload(order: Order) -> dict:
    return {
        "username": "DeepDeepBar 주문 알림",
        "allowed_mentions": {"parse": []},
        "embeds": [
            {
                "title": f"🔔 테이블 {order.table_number} 새 주문",
                "description": build_order_description(order),
                "color": 0x2ECC71,
                "fields": [
                    {
                        "name": "총 주문 금액",
                        "value": f"**{order.total_amount:,}원**",
                        "inline": True,
                    },
                    {
                        "name": "포스 등록",
                        "value": "미등록",
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
    }


async def send_order_webhook(order: Order) -> str:
    webhook_url = settings.discord_order_webhook_url

    if not webhook_url:
        raise DiscordWebhookError("Discord 주문 Webhook URL이 설정되지 않았습니다.")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                params={"wait": "true"},
                json=build_order_webhook_payload(order),
                timeout=settings.discord_order_webhook_timeout_seconds,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise DiscordWebhookError(
            f"Discord가 HTTP {error.response.status_code} 오류를 반환했습니다."
        ) from error
    except httpx.RequestError as error:
        raise DiscordWebhookError("Discord 연결에 실패했습니다.") from error
    except httpx.HTTPError as error:
        raise DiscordWebhookError(
            "Discord 요청 처리 중 오류가 발생했습니다."
        ) from error

    try:
        message_id = response.json()["id"]
    except (KeyError, TypeError, ValueError) as error:
        raise DiscordWebhookError(
            "Discord 응답에서 메시지 ID를 확인할 수 없습니다."
        ) from error

    return str(message_id)
