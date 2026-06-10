from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth_dependency import get_current_user
from app.models.user_model import User
from app.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
)
from app.schemas.user_schema import UserResponse
from app.services.auth_service import create_admin, login, logout, refresh_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    token_data = await login(db, login_data)

    response.set_cookie(
        key="refresh_token",
        value=token_data["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )

    return {
        "access_token": token_data["access_token"],
        "token_type": "Bearer",
    }


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    return await refresh_access_token(
        db=db,
        refresh_token=refresh_token,
    )


@router.get("/me")
async def read_me(current_user: Annotated[User, Depends(get_current_user)]):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
    }


@router.post("/admin", response_model=UserResponse)
async def add_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await create_admin(db)


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    result = await logout(db=db, refresh_token=refresh_token)

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=False,
        samesite="lax",
    )

    return result
