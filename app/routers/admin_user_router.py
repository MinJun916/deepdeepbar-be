import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth_dependency import require_admin
from app.models.user_model import User
from app.schemas.user_schema import CreateUserRequest, UpdateUserRequest, UserResponse
from app.services.user_service import (
    create_user,
    deactivate_user,
    get_users,
    update_user,
)

router = APIRouter(prefix="/admin/users", tags=["admin-users"])

authorized_admin = Annotated[User, Depends(require_admin)]
db = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[UserResponse])
async def read_users(
    current_user: authorized_admin,
    db: db,
):
    return await get_users(db)


@router.post("/", response_model=UserResponse)
async def add_user(
    current_user: authorized_admin,
    db: db,
    user_data: CreateUserRequest,
):
    return await create_user(db, user_data)


@router.patch("/{user_id}", response_model=UserResponse)
async def patch_user(
    user_id: uuid.UUID,
    user_data: UpdateUserRequest,
    current_user: authorized_admin,
    db: db,
):
    return await update_user(db, user_id, user_data)


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: uuid.UUID,
    current_user: authorized_admin,
    db: db,
):
    return await deactivate_user(db, user_id)
