from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    RefreshResponse,
)
from app.services.auth_service import login, refresh_access_token

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
