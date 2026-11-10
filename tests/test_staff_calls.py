import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from pydantic import ValidationError

from app.clients.discord_bot_client import build_staff_call_message_payload
from app.core.exceptions import AppError
from app.database.connection import get_db
from app.dependencies.auth_dependency import get_current_user
from app.main import app
from app.models.staff_call_model import StaffCall
from app.models.user_model import UserRole
from app.schemas.staff_call_schema import StaffCallOptionRequest
from app.services.staff_call_service import complete_staff_call, create_staff_call


class StaffCallValidationTests(TestCase):
    def test_blank_label_rejected(self):
        with self.assertRaises(ValidationError):
            StaffCallOptionRequest(label="   ")

    def test_snapshot_labels_and_completed_button(self):
        for table, label in ((None, "관리자"), (2, "2")):
            call = SimpleNamespace(
                id=uuid.uuid4(),
                table_number=table,
                label="물 주세요!",
                completed_at=None,
                created_at=datetime.now(timezone.utc),
            )
            payload = build_staff_call_message_payload(call)
            self.assertIn(f"테이블 {label} 직원 호출", payload["embeds"][0]["title"])
            self.assertFalse(payload["components"][0]["components"][0]["disabled"])
            call.completed_at = datetime.now(timezone.utc)
            self.assertTrue(
                build_staff_call_message_payload(call)["components"][0]["components"][
                    0
                ]["disabled"]
            )


class StaffCallFlowTests(IsolatedAsyncioTestCase):
    async def test_sent_pending_call_is_not_duplicated(self):
        call = StaffCall(id=uuid.uuid4(), notification_status="sent")
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: call))
        db.commit = AsyncMock()
        session = SimpleNamespace(id=uuid.uuid4(), table_number=3)
        with (
            patch(
                "app.services.staff_call_service.find_locked_active_table_session_crud",
                AsyncMock(return_value=session),
            ),
            patch(
                "app.services.staff_call_service.require_option",
                AsyncMock(return_value=SimpleNamespace(is_active=True)),
            ),
            patch(
                "app.services.staff_call_service.create_discord_message", AsyncMock()
            ) as send,
        ):
            self.assertIs(await create_staff_call(db, "token", uuid.uuid4()), call)
            send.assert_not_awaited()
            db.add.assert_not_called()

    async def test_failed_call_retried_without_new_record(self):
        call = StaffCall(
            id=uuid.uuid4(),
            notification_status="failed",
            table_number=None,
            label="물",
            created_at=datetime.now(timezone.utc),
        )
        result = MagicMock(scalar_one_or_none=lambda: call, scalar_one=lambda: call)
        db = MagicMock(
            execute=AsyncMock(return_value=result),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )
        with (
            patch(
                "app.services.staff_call_service.find_locked_active_table_session_crud",
                AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4())),
            ),
            patch(
                "app.services.staff_call_service.require_option",
                AsyncMock(return_value=SimpleNamespace(is_active=True)),
            ),
            patch(
                "app.services.staff_call_service.require_channel_id",
                return_value="channel",
            ) as require_channel,
            patch(
                "app.services.staff_call_service.create_discord_message",
                AsyncMock(return_value="message"),
            ) as send,
        ):
            self.assertIs(await create_staff_call(db, "token", uuid.uuid4()), call)
            self.assertEqual(call.notification_status, "sent")
            self.assertEqual(call.discord_message_id, "message")
            send.assert_awaited_once()
            from app.core.config import settings

            require_channel.assert_called_once_with(
                settings.discord_order_channel_id, "직원 호출"
            )
            db.add.assert_not_called()

    async def test_completion_binds_message_and_is_idempotent(self):
        call = StaffCall(id=uuid.uuid4(), discord_message_id="correct")
        db = MagicMock(
            execute=AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: call)),
            commit=AsyncMock(),
        )
        with self.assertRaises(AppError):
            await complete_staff_call(db, call.id, "forged")
        self.assertIsNone(call.completed_at)
        await complete_staff_call(db, call.id, "correct")
        first = call.completed_at
        await complete_staff_call(db, call.id, "correct")
        self.assertEqual(call.completed_at, first)

    async def test_admin_routes_reject_staff_and_anonymous(self):
        app.dependency_overrides[get_db] = lambda: AsyncMock()
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/staff-call-options/admin")
                self.assertEqual(response.status_code, 401)
                app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
                    role=UserRole.staff
                )
                response = await client.post(
                    "/staff-call-options", json={"label": "물"}
                )
                self.assertEqual(response.status_code, 403)
                response = await client.post(
                    "/staff-calls/", json={"option_id": str(uuid.uuid4())}
                )
                self.assertEqual(response.status_code, 422)
        finally:
            app.dependency_overrides.clear()


class StaffCallInteractionTests(IsolatedAsyncioTestCase):
    async def test_wrong_channel_cannot_complete_call(self):
        from app.core.config import settings
        from app.services.discord_interaction_service import handle_discord_interaction

        payload = {
            "application_id": "app",
            "guild_id": "guild",
            "channel_id": "wrong",
            "type": 3,
            "data": {"custom_id": f"staff_call_complete:{uuid.uuid4()}"},
            "member": {"user": {"id": "staff"}},
            "message": {"id": "message"},
        }
        with (
            patch.object(settings, "discord_application_id", "app"),
            patch.object(settings, "discord_guild_id", "guild"),
            patch.object(settings, "discord_table_channel_id", "legacy"),
            patch.object(settings, "discord_order_channel_id", "expected"),
            patch(
                "app.services.discord_interaction_service.complete_staff_call",
                AsyncMock(),
            ) as complete,
        ):
            response = await handle_discord_interaction(AsyncMock(), payload)
            self.assertEqual(response["data"]["flags"], 64)
            complete.assert_not_awaited()


class StaffCallRetryTests(TestCase):
    def test_retry_state_and_response_serialization(self):
        from datetime import timedelta

        from app.schemas.staff_call_schema import StaffCallResponse

        now = datetime.now(timezone.utc)
        with patch("app.models.staff_call_model.get_utc_now", return_value=now):
            for status, attempted, completed, expected in (
                ("pending", None, None, True),
                ("failed", now, None, True),
                ("sending", None, None, True),
                ("sending", now - timedelta(seconds=61), None, True),
                ("sending", now - timedelta(seconds=60), None, True),
                ("sending", now - timedelta(seconds=59), None, False),
                ("sent", now, None, False),
                ("failed", now, now, False),
            ):
                call = StaffCall(
                    id=uuid.uuid4(),
                    option_id=uuid.uuid4(),
                    label="물",
                    table_number=None,
                    created_at=now,
                    completed_at=completed,
                    notification_status=status,
                    last_attempted_at=attempted,
                )
                self.assertEqual(call.retry_available, expected)
                self.assertEqual(
                    StaffCallResponse.model_validate(call).model_dump()[
                        "retry_available"
                    ],
                    expected,
                )


class StaffCallCreationTests(IsolatedAsyncioTestCase):
    async def test_no_unfinished_call_creates_snapshot_for_new_or_completed_request(
        self,
    ):
        db = MagicMock(commit=AsyncMock())
        existing_result = MagicMock(scalar_one_or_none=lambda: None)
        saved_result = MagicMock(scalar_one=lambda: db.add.call_args.args[0])
        db.execute = AsyncMock(side_effect=[existing_result, saved_result])

        async def commit():
            if db.add.called:
                call = db.add.call_args.args[0]
                call.id = call.id or uuid.uuid4()
                call.created_at = call.created_at or datetime.now(timezone.utc)

        db.commit.side_effect = commit
        session = SimpleNamespace(id=uuid.uuid4(), table_number=None)
        option_id = uuid.uuid4()
        with (
            patch(
                "app.services.staff_call_service.find_locked_active_table_session_crud",
                AsyncMock(return_value=session),
            ),
            patch(
                "app.services.staff_call_service.require_option",
                AsyncMock(
                    return_value=SimpleNamespace(is_active=True, label="현재 요청 문구")
                ),
            ),
            patch(
                "app.services.staff_call_service.require_channel_id",
                return_value="channel",
            ) as require_channel,
            patch(
                "app.services.staff_call_service.create_discord_message",
                AsyncMock(return_value="message"),
            ),
        ):
            call = await create_staff_call(db, "token", option_id)
            from app.core.config import settings

            require_channel.assert_called_once_with(
                settings.discord_order_channel_id, "직원 호출"
            )
            self.assertEqual(call.label, "현재 요청 문구")
            self.assertEqual(call.table_session_id, session.id)
            self.assertIsNone(call.table_number)
            self.assertEqual(call.option_id, option_id)
            self.assertEqual(call.notification_status, "sent")
            db.add.assert_called_once()


class StaffCallOrderChannelTests(IsolatedAsyncioTestCase):
    async def test_order_and_existing_table_messages_can_complete(self):
        from app.core.config import settings
        from app.services.discord_interaction_service import handle_discord_interaction

        for channel in ("order", "legacy-table"):
            call_id = uuid.uuid4()
            payload = {
                "application_id": "app",
                "guild_id": "guild",
                "channel_id": channel,
                "type": 3,
                "data": {"custom_id": f"staff_call_complete:{call_id}"},
                "member": {"user": {"id": "staff"}},
                "message": {"id": "message"},
            }
            db = AsyncMock()
            with (
                patch.object(settings, "discord_application_id", "app"),
                patch.object(settings, "discord_guild_id", "guild"),
                patch.object(settings, "discord_order_channel_id", "order"),
                patch.object(settings, "discord_table_channel_id", "legacy-table"),
                patch(
                    "app.services.discord_interaction_service.complete_staff_call",
                    AsyncMock(),
                ) as complete,
                patch(
                    "app.services.discord_interaction_service.build_staff_call_message_payload",
                    return_value={},
                ),
            ):
                response = await handle_discord_interaction(db, payload)
                self.assertEqual(response["type"], 7)
                complete.assert_awaited_once_with(db, call_id, "message")
