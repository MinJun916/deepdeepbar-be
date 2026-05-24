import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import INTERNAL_SERVER_ERROR
from app.core.exceptions import AppError
from app.crud.queries.user_query import get_users_query
from app.models.user_model import User


async def find_users(db: AsyncSession):
    query = get_users_query().order_by(User.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


async def find_user_by_id(
    db: AsyncSession,
    user_id: uuid.UUID,
):
    query = get_users_query().where(User.id == user_id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def find_user_by_email(
    db: AsyncSession,
    email: str,
):
    query = get_users_query().where(User.email == email)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_user_crud(
    db: AsyncSession,
    user: User,
):
    try:
        db.add(user)

        await db.commit()
        await db.refresh(user)

        return user

    except Exception as error:
        await db.rollback()
        raise AppError(status_code=INTERNAL_SERVER_ERROR, message=str(error))
