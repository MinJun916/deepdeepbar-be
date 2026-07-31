import uuid
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import FORBIDDEN, UNAUTHORIZED
from app.core.exceptions import AppError
from app.core.jwt import decode_token
from app.database.connection import get_db
from app.models.user_model import User, UserRole

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_schema)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        payload = decode_token(token)

    except jwt.PyJWTError:
        raise AppError(status_code=UNAUTHORIZED, message="유효하지 않은 토큰입니다.")

    if payload.get("type") != "access":
        raise AppError(status_code=UNAUTHORIZED, message="access token이 아닙니다.")

    user_id_value = payload.get("sub")

    try:
        user_id = uuid.UUID(user_id_value)
    except (TypeError, ValueError):
        raise AppError(
            status_code=UNAUTHORIZED,
            message="토큰 정보가 올바르지 않습니다.",
        ) from None

    result = await db.execute(select(User).where(User.id == user_id))

    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="유저를 찾을 수 없습니다.",
        )

    return user


async def require_admin(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.role != UserRole.admin:
        raise AppError(
            status_code=FORBIDDEN,
            message="관리자 권한이 필요합니다.",
        )

    return current_user


async def require_staff_or_admin(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in [UserRole.admin, UserRole.staff]:
        raise AppError(
            status_code=FORBIDDEN,
            message="접근 권한이 없습니다.",
        )

    return current_user
