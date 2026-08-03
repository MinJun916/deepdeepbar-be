import asyncio

from app.clients.discord_bot_client import DiscordBotError
from app.clients.discord_command_client import register_order_mode_command


async def register_commands() -> None:
    command = await register_order_mode_command()
    print(f"Discord 길드 명령어 등록 완료: /{command['name']} (ID: {command['id']})")


def main() -> None:
    try:
        asyncio.run(register_commands())
    except DiscordBotError as error:
        raise SystemExit(f"Discord 명령어 등록 실패: {error}") from error


if __name__ == "__main__":
    main()
