from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
)
from app.services.auth_service import login, refresh_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    return await login(db, login_data)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    refresh_data: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    return await refresh_access_token(
        db=db,
        refresh_token=refresh_data.refresh_token,
    )
