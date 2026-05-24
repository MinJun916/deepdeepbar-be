import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import BAD_REQUEST, INTERNAL_SERVER_ERROR, NOT_FOUND
from app.core.exceptions import AppError
from app.core.security import hash_token
from app.crud.user_crud import (
    create_user_crud,
    find_user_by_email,
    find_user_by_id,
    find_users,
)
from app.models.user_model import User
from app.schemas.user_schema import CreateUserRequest, UpdateUserRequest


async def get_users(db: AsyncSession):
    return await find_users(db)


async def create_user(
    db: AsyncSession,
    user_data: CreateUserRequest,
):
    try:
        existing_user = await find_user_by_email(db, user_data.email)

        if existing_user is not None:
            raise AppError(
                status_code=BAD_REQUEST, message="이미 존재하는 이메일입니다."
            )

        user = User(
            email=user_data.email,
            password_hash=hash_token(user_data.password),
            name=user_data.name,
            role=user_data.role,
            is_active=True,
        )

        return await create_user_crud(db, user)

    except AppError:
        raise

    except Exception as error:
        raise AppError(status_code=INTERNAL_SERVER_ERROR, message=str(error))


async def update_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    user_data: UpdateUserRequest,
):
    try:
        user = await find_user_by_id(db, user_id)

        if user is None:
            raise AppError(status_code=NOT_FOUND, message="User not found")

        update_data = user_data.model_dump(
            exclude_unset=True,
        )

        for key, value in update_data.items():
            setattr(user, key, value)

        await db.commit()
        await db.refresh(user)

        return user

    except AppError:
        raise

    except Exception as error:
        raise AppError(status_code=INTERNAL_SERVER_ERROR, message=str(error))


async def deactivate_user(
    db: AsyncSession,
    user_id: uuid.UUID,
):
    try:
        user = await find_user_by_id(db, user_id)

        if user is None:
            raise AppError(status_code=NOT_FOUND, message="User not found")

        user.is_active = False
        await db.commit()
        await db.refresh(user)

        return user

    except AppError:
        raise

    except Exception as error:
        raise AppError(status_code=INTERNAL_SERVER_ERROR, message=str(error))
