import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token_model import RefreshToken
from app.models.user_model import User


async def find_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def find_user_by_id(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def find_refresh_token_by_token_hash(
    db: AsyncSession, token_hash: str
) -> RefreshToken | None:
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.deleted_at.is_(None),
        )
        .with_for_update()
    )

    return result.scalar_one_or_none()


async def revoke_refresh_token_crud(
    db: AsyncSession,
    token_hash: str,
) -> RefreshToken | None:
    refresh_token = await find_refresh_token_by_token_hash(db, token_hash)

    if refresh_token is None:
        return None

    refresh_token.revoked_at = datetime.now(timezone.utc)

    db.add(refresh_token)
    await db.commit()
    await db.refresh(refresh_token)

    return refresh_token
