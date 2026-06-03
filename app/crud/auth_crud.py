import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
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
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )

    return result.scalar_one_or_none()


async def create_admin_crud(
    db: AsyncSession,
    admin_data: dict,
):
    admin = User(
        email=admin_data["email"],
        password_hash=hash_password(admin_data["password_hash"]),
        name=admin_data["name"],
        role=admin_data["role"],
        is_active=admin_data["is_active"],
    )

    db.add(admin)

    await db.commit()
    await db.refresh(admin)

    return admin
