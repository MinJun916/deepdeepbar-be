from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.connection import get_db
from app.dependencies.auth_dependency import get_current_user
from app.models.user_model import User
from app.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
)
from app.services.auth_service import login, logout, refresh_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/auth"


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.auth_refresh_cookie_secure,
        samesite=settings.auth_refresh_cookie_samesite,
        domain=settings.auth_refresh_cookie_domain,
        path=REFRESH_COOKIE_PATH,
        max_age=settings.refresh_cookie_max_age_seconds,
    )


def delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.auth_refresh_cookie_secure,
        samesite=settings.auth_refresh_cookie_samesite,
        domain=settings.auth_refresh_cookie_domain,
        path=REFRESH_COOKIE_PATH,
    )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    token_data = await login(db, login_data)

    set_refresh_cookie(response, token_data["refresh_token"])

    return {
        "access_token": token_data["access_token"],
        "token_type": "Bearer",
    }


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    token_data = await refresh_access_token(
        db=db,
        refresh_token=refresh_token,
    )
    set_refresh_cookie(response, token_data["refresh_token"])
    return {
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
    }


@router.get("/me")
async def read_me(current_user: Annotated[User, Depends(get_current_user)]):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
    }


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    result = await logout(db=db, refresh_token=refresh_token)

    delete_refresh_cookie(response)

    return result
