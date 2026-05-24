from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import FORBIDDEN, UNAUTHORIZED
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.core.security import hash_token, verify_password
from app.models.refresh_token_model import RefreshToken
from app.models.user_model import User


async def login(db: AsyncSession, login_data):
    result = await db.execute(select(User).where(User.email == login_data.email))

    user = result.scalar_one_or_none()

    if user is None:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="Unauthorized",
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

    refresh_token = create_refresh_token(
        user_id=user.id,
    )

    refresh_token_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )

    db.add(refresh_token_row)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
):
    try:
        payload = decode_token(refresh_token)

    except jwt.PyJWTError:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="유효하지 않은 토큰입니다.",
        )

    if payload.get("type") != "refresh":
        raise AppError(status_code=UNAUTHORIZED, message="유효하지 않은 토큰입니다.")

    user_id = payload.get("sub")

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(refresh_token),
            RefreshToken.revoked_at.is_(None),
        )
    )

    saved_token = result.scalar_one_or_none()

    if saved_token is None:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="사용할 수 없는 refresh token입니다.",
        )

    result = await db.execute(select(User).where(User.id == user_id))

    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="유저를 찾을 수 없습니다.",
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
    }
