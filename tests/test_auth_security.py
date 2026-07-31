import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import Response
from pydantic import ValidationError

from app.constants.status_code import UNAUTHORIZED
from app.core.config import Settings, settings
from app.core.exceptions import AppError
from app.core.jwt import create_refresh_token, decode_token
from app.main import app
from app.routers.auth_router import delete_refresh_cookie, set_refresh_cookie
from app.services.auth_service import refresh_access_token


class AuthCookieTests(TestCase):
    def test_refresh_cookie_uses_consistent_secure_attributes(self):
        response = Response()
        set_refresh_cookie(response, "refresh-token")
        cookie = response.headers["set-cookie"].lower()

        self.assertIn("httponly", cookie)
        self.assertIn("path=/auth", cookie)
        self.assertIn(f"samesite={settings.auth_refresh_cookie_samesite}", cookie)

        if settings.auth_refresh_cookie_secure:
            self.assertIn("secure", cookie)

        delete_response = Response()
        delete_refresh_cookie(delete_response)
        deleted_cookie = delete_response.headers["set-cookie"].lower()

        self.assertIn("max-age=0", deleted_cookie)
        self.assertIn("path=/auth", deleted_cookie)
        self.assertIn(
            f"samesite={settings.auth_refresh_cookie_samesite}",
            deleted_cookie,
        )

    def test_refresh_tokens_have_unique_jti(self):
        user_id = uuid.uuid4()
        first_token = create_refresh_token(user_id)
        second_token = create_refresh_token(user_id)

        self.assertNotEqual(first_token, second_token)
        self.assertNotEqual(
            decode_token(first_token)["jti"],
            decode_token(second_token)["jti"],
        )

    def test_public_admin_bootstrap_route_is_removed(self):
        self.assertNotIn("/auth/admin", app.openapi()["paths"])

    def test_samesite_none_requires_secure_cookie(self):
        with self.assertRaises(ValidationError):
            Settings(
                database_url="postgresql+asyncpg://test:test@localhost/test",
                jwt_secret_key="test-secret",
                jwt_algorithm="HS256",
                access_token_expire_minutes=30,
                refresh_token_expire_days=7,
                auth_refresh_cookie_secure=False,
                auth_refresh_cookie_samesite="none",
                _env_file=None,
            )


class RefreshTokenTests(IsolatedAsyncioTestCase):
    async def test_missing_refresh_token_is_rejected(self):
        with self.assertRaises(AppError) as raised:
            await refresh_access_token(AsyncMock(), None)

        self.assertEqual(raised.exception.status_code, int(UNAUTHORIZED))

    async def test_refresh_token_is_rotated(self):
        user_id = uuid.uuid4()
        old_token = create_refresh_token(user_id)
        saved_token = SimpleNamespace(
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            revoked_at=None,
        )
        user = SimpleNamespace(id=user_id, role="admin", is_active=True)
        rotated_row = SimpleNamespace()
        db = MagicMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()

        with (
            patch(
                "app.services.auth_service.find_refresh_token_by_token_hash",
                AsyncMock(return_value=saved_token),
            ),
            patch(
                "app.services.auth_service.find_user_by_id",
                AsyncMock(return_value=user),
            ),
            patch(
                "app.services.auth_service.create_access_token",
                return_value="new-access-token",
            ),
            patch(
                "app.services.auth_service.create_refresh_token_record",
                return_value=("new-refresh-token", rotated_row),
            ),
        ):
            result = await refresh_access_token(db, old_token)

        self.assertEqual(result["access_token"], "new-access-token")
        self.assertEqual(result["refresh_token"], "new-refresh-token")
        self.assertIsNotNone(saved_token.revoked_at)
        db.add.assert_called_once_with(rotated_row)
        db.commit.assert_awaited_once()
        db.rollback.assert_not_awaited()

    async def test_revoked_refresh_token_is_rejected(self):
        token = create_refresh_token(uuid.uuid4())

        with patch(
            "app.services.auth_service.find_refresh_token_by_token_hash",
            AsyncMock(return_value=None),
        ):
            with self.assertRaises(AppError) as raised:
                await refresh_access_token(AsyncMock(), token)

        self.assertEqual(raised.exception.status_code, int(UNAUTHORIZED))

    async def test_expired_refresh_token_is_revoked(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        saved_token = SimpleNamespace(
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            revoked_at=None,
        )
        db = MagicMock()
        db.commit = AsyncMock()

        with patch(
            "app.services.auth_service.find_refresh_token_by_token_hash",
            AsyncMock(return_value=saved_token),
        ):
            with self.assertRaises(AppError) as raised:
                await refresh_access_token(db, token)

        self.assertEqual(raised.exception.status_code, int(UNAUTHORIZED))
        self.assertIsNotNone(saved_token.revoked_at)
        db.commit.assert_awaited_once()

    async def test_inactive_user_cannot_refresh(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        saved_token = SimpleNamespace(
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            revoked_at=None,
        )
        inactive_user = SimpleNamespace(id=user_id, role="admin", is_active=False)

        with (
            patch(
                "app.services.auth_service.find_refresh_token_by_token_hash",
                AsyncMock(return_value=saved_token),
            ),
            patch(
                "app.services.auth_service.find_user_by_id",
                AsyncMock(return_value=inactive_user),
            ),
        ):
            with self.assertRaises(AppError) as raised:
                await refresh_access_token(MagicMock(), token)

        self.assertEqual(raised.exception.status_code, int(UNAUTHORIZED))
