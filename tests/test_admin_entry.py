import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

import httpx

from app.clients.discord_bot_client import (
    build_order_message_payload,
    build_table_session_message_payload,
)
from app.database.connection import get_db
from app.dependencies.auth_dependency import get_current_user
from app.main import app
from app.models.user_model import UserRole
from app.services.table_session_service import enter_table


def session_data(table_number=None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        table_number=table_number,
        created_at=datetime.now(timezone.utc),
        checked_out_at=None,
        checked_out_by_user_id=None,
        checked_out_by_discord_user_id=None,
        is_active=True,
    )


class AdminEntryTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

    async def asyncTearDown(self):
        app.dependency_overrides.clear()
        await self.client.aclose()

    async def test_entry_requires_admin(self):
        with patch(
            "app.routers.table_session_router.enter_table", AsyncMock()
        ) as enter:
            response = await self.client.post("/table-sessions/admin-enter")
            self.assertEqual(response.status_code, 401)
            app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
                role=UserRole.staff
            )
            response = await self.client.post("/table-sessions/admin-enter")
            self.assertEqual(response.status_code, 403)
            enter.assert_not_awaited()

    async def test_admin_entry_returns_null_table_and_session_token(self):
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            role=UserRole.admin
        )
        result = vars(session_data()) | {"session_token": "admin-session-token"}
        with patch(
            "app.routers.table_session_router.enter_table",
            AsyncMock(return_value=result),
        ) as enter:
            response = await self.client.post("/table-sessions/admin-enter")
            self.assertEqual(response.status_code, 201)
            self.assertIsNone(response.json()["table_number"])
            self.assertEqual(response.json()["session_token"], "admin-session-token")
            enter.assert_awaited_once_with(self.db, None)

    async def test_regular_entry_cannot_omit_or_forge_admin_table(self):
        for body in ({}, {"table_number": None}, {"table_number": 0}):
            response = await self.client.post("/table-sessions/enter", json=body)
            self.assertEqual(response.status_code, 422)

    async def test_admin_session_uses_existing_token_and_notification_flow(self):
        with (
            patch(
                "app.services.table_session_service.create_table_session_crud",
                AsyncMock(return_value=session_data()),
            ) as create,
            patch(
                "app.services.table_session_service.try_dispatch_discord_table_session_notification",
                AsyncMock(),
            ) as notify,
        ):
            result = await enter_table(self.db, None)
            self.assertIsNone(create.call_args.args[1])
            self.assertNotEqual(result["session_token"], create.call_args.args[2])
            notify.assert_awaited_once_with(self.db, result["id"])


class AdminNotificationTests(TestCase):
    def test_admin_and_regular_order_labels(self):
        for number, label in ((None, "관리자"), (3, "3")):
            order = SimpleNamespace(
                id=uuid.uuid4(),
                table_number=number,
                items=[],
                is_pos_registered=False,
                total_amount=0,
                created_at=datetime.now(timezone.utc),
            )
            payload = build_order_message_payload(order)
            self.assertEqual(
                payload["embeds"][0]["title"], f"🔔 테이블 {label} 새 주문"
            )
            session_payload = build_table_session_message_payload(session_data(number))
            self.assertEqual(
                session_payload["embeds"][0]["title"], f"🪑 테이블 {label} 체크인"
            )
