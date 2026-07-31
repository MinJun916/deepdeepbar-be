import secrets
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.crud.table_session_crud import (
    checkout_table_session_crud,
    create_table_session_crud,
    find_active_table_session_by_token_hash_crud,
    find_table_sessions_crud,
)
from app.models.base_model import get_utc_now
from app.models.table_session_model import TableSession


async def enter_table(
    db: AsyncSession,
    table_number: int,
) -> dict:
    session_token = secrets.token_urlsafe(32)
    table_session = await create_table_session_crud(
        db,
        table_number,
        hash_token(session_token),
    )

    return {
        "id": table_session.id,
        "table_number": table_session.table_number,
        "created_at": table_session.created_at,
        "checked_out_at": table_session.checked_out_at,
        "checked_out_by_user_id": table_session.checked_out_by_user_id,
        "is_active": table_session.is_active,
        "session_token": session_token,
    }


async def get_current_table_session(
    db: AsyncSession,
    session_token: str,
) -> TableSession:
    return await find_active_table_session_by_token_hash_crud(
        db,
        hash_token(session_token),
    )


async def get_table_sessions(
    db: AsyncSession,
    active_only: bool,
) -> list[TableSession]:
    return await find_table_sessions_crud(db, active_only)


async def checkout_table_session(
    db: AsyncSession,
    table_session_id: uuid.UUID,
    checked_out_by_user_id: uuid.UUID,
) -> TableSession:
    return await checkout_table_session_crud(
        db,
        table_session_id,
        checked_out_by_user_id,
        get_utc_now(),
    )
