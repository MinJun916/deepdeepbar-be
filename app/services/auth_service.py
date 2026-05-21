from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jwt import create_access_token, create_refresh_token
from app.core.security import hash_token, verify_password
from app.models.refresh_token_model import RefreshToken
from app.models.user_model import User


async def login(db: AsyncSession, login_data):
    result = await db.execute(select(User).where(User.email == login_data.email))

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )

    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="비밀번호 또는 이메일이 일치하지 않습니다.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="비활성화 처리된 유저입니다.",
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
