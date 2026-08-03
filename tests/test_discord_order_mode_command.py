from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, MagicMock, patch

from app.clients.discord_command_client import register_order_mode_command
from app.constants.discord_command import (
    ORDER_MODE_COMMAND_NAME,
    ORDER_MODE_ENABLED_VALUE,
    ORDER_MODE_MENU_ONLY_VALUE,
    ORDER_MODE_OPTION_NAME,
    build_order_mode_command_payload,
)
from app.core.config import settings
from app.services.discord_interaction_service import handle_discord_interaction


class DiscordOrderModeCommandTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_application_id = settings.discord_application_id
        self.original_guild_id = settings.discord_guild_id
        self.original_table_channel_id = settings.discord_table_channel_id
        settings.discord_application_id = "application-1"
        settings.discord_guild_id = "guild-1"
        settings.discord_table_channel_id = "table-channel-1"

    def tearDown(self):
        settings.discord_application_id = self.original_application_id
        settings.discord_guild_id = self.original_guild_id
        settings.discord_table_channel_id = self.original_table_channel_id

    @staticmethod
    def build_payload(
        mode: str = ORDER_MODE_ENABLED_VALUE,
        *,
        channel_id: str = "table-channel-1",
    ) -> dict:
        return {
            "application_id": "application-1",
            "guild_id": "guild-1",
            "channel_id": channel_id,
            "type": 2,
            "data": {
                "name": ORDER_MODE_COMMAND_NAME,
                "options": [
                    {
                        "name": ORDER_MODE_OPTION_NAME,
                        "value": mode,
                    }
                ],
            },
            "member": {"user": {"id": "discord-user-1"}},
        }

    async def test_channel_user_can_enable_ordering(self):
        db = AsyncMock()

        with patch(
            "app.services.discord_interaction_service.update_order_mode",
            AsyncMock(),
        ) as update_order_mode:
            response = await handle_discord_interaction(db, self.build_payload())

        update_order_mode.assert_awaited_once_with(db, True)
        self.assertEqual(response["type"], 4)
        self.assertEqual(response["data"]["flags"], 64)
        self.assertIn("주문 가능", response["data"]["content"])

    async def test_channel_user_can_enable_menu_only_mode(self):
        db = AsyncMock()

        with patch(
            "app.services.discord_interaction_service.update_order_mode",
            AsyncMock(),
        ) as update_order_mode:
            response = await handle_discord_interaction(
                db,
                self.build_payload(ORDER_MODE_MENU_ONLY_VALUE),
            )

        update_order_mode.assert_awaited_once_with(db, False)
        self.assertIn("메뉴판 전용", response["data"]["content"])

    async def test_command_is_rejected_outside_configured_channel(self):
        with patch(
            "app.services.discord_interaction_service.update_order_mode",
            AsyncMock(),
        ) as update_order_mode:
            response = await handle_discord_interaction(
                AsyncMock(),
                self.build_payload(channel_id="another-channel"),
            )

        update_order_mode.assert_not_awaited()
        self.assertEqual(response["data"]["flags"], 64)
        self.assertIn("허용되지 않은", response["data"]["content"])

    async def test_invalid_mode_is_rejected(self):
        with patch(
            "app.services.discord_interaction_service.update_order_mode",
            AsyncMock(),
        ) as update_order_mode:
            response = await handle_discord_interaction(
                AsyncMock(),
                self.build_payload("invalid"),
            )

        update_order_mode.assert_not_awaited()
        self.assertIn("선택값이 올바르지", response["data"]["content"])


class DiscordOrderModeCommandPayloadTests(TestCase):
    def test_registration_payload_allows_every_channel_user(self):
        payload = build_order_mode_command_payload()
        option = payload["options"][0]

        self.assertEqual(payload["name"], ORDER_MODE_COMMAND_NAME)
        self.assertNotIn("default_member_permissions", payload)
        self.assertTrue(option["required"])
        self.assertEqual(
            option["choices"],
            [
                {"name": "주문 가능", "value": ORDER_MODE_ENABLED_VALUE},
                {"name": "메뉴판 전용", "value": ORDER_MODE_MENU_ONLY_VALUE},
            ],
        )


class DiscordOrderModeCommandRegistrationTests(IsolatedAsyncioTestCase):
    async def test_registers_guild_command_with_bot_token(self):
        response = MagicMock()
        response.json.return_value = {
            "id": "command-1",
            "name": ORDER_MODE_COMMAND_NAME,
        }
        client = AsyncMock()
        client.post.return_value = response
        client_context = AsyncMock()
        client_context.__aenter__.return_value = client

        with (
            patch(
                "app.clients.discord_command_client.require_bot_token",
                return_value="bot-token",
            ),
            patch(
                "app.clients.discord_command_client.require_command_registration_ids",
                return_value=("application-1", "guild-1"),
            ),
            patch(
                "app.clients.discord_command_client.httpx.AsyncClient",
                return_value=client_context,
            ),
        ):
            command = await register_order_mode_command()

        self.assertEqual(
            command,
            {"id": "command-1", "name": ORDER_MODE_COMMAND_NAME},
        )
        client.post.assert_awaited_once()
        request = client.post.await_args
        self.assertEqual(
            request.args[0],
            (
                "https://discord.com/api/v10/applications/application-1"
                "/guilds/guild-1/commands"
            ),
        )
        self.assertEqual(
            request.kwargs["headers"],
            {"Authorization": "Bot bot-token"},
        )
        self.assertEqual(
            request.kwargs["json"],
            build_order_mode_command_payload(),
        )
