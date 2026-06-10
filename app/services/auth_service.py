from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import BAD_REQUEST, FORBIDDEN, UNAUTHORIZED
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.core.security import hash_token, verify_password
from app.crud.auth_crud import (
    create_admin_crud,
    find_refresh_token_by_token_hash,
    find_user_by_email,
    find_user_by_id,
    revoke_refresh_token_crud,
)
from app.models.refresh_token_model import RefreshToken
from app.models.user_model import UserRole


async def login(db: AsyncSession, login_data):
    user = await find_user_by_email(db, login_data.email)

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

    saved_token = await find_refresh_token_by_token_hash(
        db,
        hash_token(refresh_token),
    )

    if saved_token is None:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="사용할 수 없는 refresh token입니다.",
        )

    user = await find_user_by_id(db, user_id)

    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
    }


async def create_admin(
    db: AsyncSession,
):
    admin_data = {
        "email": "admin@deepdeep.com",
        "password_hash": "deepdeep",
        "name": "Admin",
        "role": UserRole.admin,
        "is_active": True,
    }

    if await find_user_by_email(db, admin_data["email"]) is not None:
        raise AppError(
            status_code=BAD_REQUEST,
            message="이미 존재하는 이메일입니다.",
        )

    return await create_admin_crud(db, admin_data)


async def logout(
    db: AsyncSession,
    refresh_token: str | None,
):
    if refresh_token is not None:
        await revoke_refresh_token_crud(db, hash_token(refresh_token))

    return {
        "message": "로그아웃 되었습니다.",
    }
