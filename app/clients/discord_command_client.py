from __future__ import annotations

import httpx

from app.clients.discord_bot_client import (
    DISCORD_API_BASE_URL,
    DiscordBotError,
    require_bot_token,
)
from app.constants.discord_command import build_order_mode_command_payload
from app.core.config import settings


def require_command_registration_ids() -> tuple[str, str]:
    application_id = settings.discord_application_id
    guild_id = settings.discord_guild_id

    if not application_id:
        raise DiscordBotError("Discord Application ID가 설정되지 않았습니다.")

    if not guild_id:
        raise DiscordBotError("Discord Guild ID가 설정되지 않았습니다.")

    return application_id, guild_id


async def register_order_mode_command() -> dict:
    bot_token = require_bot_token()
    application_id, guild_id = require_command_registration_ids()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                (
                    f"{DISCORD_API_BASE_URL}/applications/{application_id}"
                    f"/guilds/{guild_id}/commands"
                ),
                headers={"Authorization": f"Bot {bot_token}"},
                json=build_order_mode_command_payload(),
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
        command = response.json()
        return {
            "id": str(command["id"]),
            "name": str(command["name"]),
        }
    except (KeyError, TypeError, ValueError) as error:
        raise DiscordBotError(
            "Discord 응답에서 등록된 명령어를 확인할 수 없습니다."
        ) from error
