import uuid
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import FORBIDDEN, UNAUTHORIZED
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.core.security import hash_token, verify_password
from app.crud.auth_crud import (
    find_refresh_token_by_token_hash,
    find_user_by_email,
    find_user_by_id,
    revoke_refresh_token_crud,
)
from app.models.refresh_token_model import RefreshToken
from app.schemas.auth_schema import LoginRequest


def create_refresh_token_record(user_id: uuid.UUID) -> tuple[str, RefreshToken]:
    refresh_token = create_refresh_token(user_id=user_id)
    return refresh_token, RefreshToken(
        user_id=user_id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )


async def login(db: AsyncSession, login_data: LoginRequest):
    user = await find_user_by_email(db, login_data.email)

    if user is None:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="비밀번호 또는 이메일이 일치하지 않습니다.",
        )

    if not verify_password(login_data.password, user.password_hash):
        raise AppError(
            status_code=UNAUTHORIZED,
            message="비밀번호 또는 이메일이 일치하지 않습니다.",
        )

    if not user.is_active:
        raise AppError(
            status_code=FORBIDDEN,
            message="비활성화 처리된 유저입니다.",
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    refresh_token, refresh_token_row = create_refresh_token_record(user.id)

    db.add(refresh_token_row)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str | None,
):
    if not refresh_token:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="refresh token이 필요합니다.",
        )

    try:
        payload = decode_token(refresh_token)

    except (jwt.PyJWTError, TypeError):
        raise AppError(
            status_code=UNAUTHORIZED,
            message="유효하지 않은 토큰입니다.",
        )

    if payload.get("type") != "refresh":
        raise AppError(status_code=UNAUTHORIZED, message="유효하지 않은 토큰입니다.")

    user_id_value = payload.get("sub")

    try:
        user_id = uuid.UUID(user_id_value)
    except (TypeError, ValueError):
        raise AppError(
            status_code=UNAUTHORIZED,
            message="유효하지 않은 토큰입니다.",
        ) from None

    saved_token = await find_refresh_token_by_token_hash(
        db,
        hash_token(refresh_token),
    )

    if saved_token is None:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="사용할 수 없는 refresh token입니다.",
        )

    now = datetime.now(timezone.utc)

    if saved_token.expires_at <= now:
        saved_token.revoked_at = now
        await db.commit()
        raise AppError(
            status_code=UNAUTHORIZED,
            message="만료된 refresh token입니다.",
        )

    user = await find_user_by_id(db, user_id)

    if user is None or not user.is_active:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="유저를 찾을 수 없습니다.",
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    rotated_refresh_token, rotated_token_row = create_refresh_token_record(user.id)
    saved_token.revoked_at = now
    db.add(rotated_token_row)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return {
        "access_token": access_token,
        "refresh_token": rotated_refresh_token,
        "token_type": "Bearer",
    }


async def logout(
    db: AsyncSession,
    refresh_token: str | None,
):
    if refresh_token is not None:
        await revoke_refresh_token_crud(db, hash_token(refresh_token))

    return {
        "message": "로그아웃 되었습니다.",
    }
