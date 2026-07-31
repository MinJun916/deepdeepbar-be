import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth_dependency import require_admin
from app.models.user_model import User
from app.schemas.table_session_schema import (
    EnterTableRequest,
    EnterTableResponse,
    TableSessionResponse,
)
from app.services.table_session_service import (
    checkout_table_session,
    enter_table,
    get_current_table_session,
    get_table_sessions,
)

router = APIRouter(prefix="/table-sessions", tags=["table-sessions"])

db = Annotated[AsyncSession, Depends(get_db)]
authorized_admin = Annotated[User, Depends(require_admin)]
table_session_token = Annotated[str, Header(alias="X-Table-Session-Token")]


@router.post(
    "/enter",
    response_model=EnterTableResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enter_table_session(
    table_data: EnterTableRequest,
    db: db,
):
    return await enter_table(db, table_data.table_number)


@router.get("/current", response_model=TableSessionResponse)
async def read_current_table_session(
    session_token: table_session_token,
    db: db,
):
    return await get_current_table_session(db, session_token)


@router.get("/", response_model=list[TableSessionResponse])
async def read_table_sessions(
    current_user: authorized_admin,
    db: db,
    active_only: Annotated[bool, Query()] = True,
):
    return await get_table_sessions(db, active_only)


@router.patch(
    "/{table_session_id}/checkout",
    response_model=TableSessionResponse,
)
async def checkout_table(
    table_session_id: uuid.UUID,
    current_user: authorized_admin,
    db: db,
):
    return await checkout_table_session(
        db,
        table_session_id,
        current_user.id,
    )
