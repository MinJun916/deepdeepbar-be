from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="access token이 아닙니다.")

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="토큰 정보가 올바르지 않습니다.",
        )

    result = await db.execute(select(User).where(User.id == user_id))

    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="유저를 찾을 수 없습니다.",
        )

    return user


async def require_admin(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다.",
        )

    return current_user


async def require_staff_or_admin(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in [UserRole.admin, UserRole.staff]:
        raise HTTPException(
            status_code=403,
            detail="접근 권한이 없습니다.",
        )

    return current_user
