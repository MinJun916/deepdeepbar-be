import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import CONFLICT, NOT_FOUND, UNAUTHORIZED
from app.core.exceptions import AppError
from app.models.table_session_model import TableSession


async def create_table_session_crud(
    db: AsyncSession,
    table_number: int,
    token_hash: str,
) -> TableSession:
    table_session = TableSession(
        table_number=table_number,
        token_hash=token_hash,
    )
    db.add(table_session)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppError(
            status_code=CONFLICT,
            message="현재 사용 중인 테이블 번호입니다.",
        )

    await db.refresh(table_session)
    return table_session


async def find_active_table_session_by_token_hash_crud(
    db: AsyncSession,
    token_hash: str,
) -> TableSession:
    result = await db.execute(
        select(TableSession).where(
            TableSession.token_hash == token_hash,
            TableSession.checked_out_at.is_(None),
        )
    )
    table_session = result.scalar_one_or_none()

    if table_session is None:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="유효한 테이블 세션을 찾을 수 없습니다.",
        )

    return table_session


async def find_table_sessions_crud(
    db: AsyncSession,
    active_only: bool,
) -> list[TableSession]:
    query = select(TableSession).order_by(TableSession.created_at.desc())

    if active_only:
        query = query.where(TableSession.checked_out_at.is_(None))

    result = await db.execute(query)
    return list(result.scalars().all())


async def checkout_table_session_crud(
    db: AsyncSession,
    table_session_id: uuid.UUID,
    checked_out_by_user_id: uuid.UUID,
    checked_out_at: datetime,
) -> TableSession:
    result = await db.execute(
        update(TableSession)
        .where(
            TableSession.id == table_session_id,
            TableSession.checked_out_at.is_(None),
        )
        .values(
            checked_out_at=checked_out_at,
            checked_out_by_user_id=checked_out_by_user_id,
            updated_at=checked_out_at,
        )
        .returning(TableSession)
    )
    table_session = result.scalar_one_or_none()

    if table_session is None:
        existing_result = await db.execute(
            select(TableSession.id).where(TableSession.id == table_session_id)
        )

        if existing_result.scalar_one_or_none() is None:
            raise AppError(
                status_code=NOT_FOUND,
                message="테이블 세션을 찾을 수 없습니다.",
            )

        raise AppError(
            status_code=CONFLICT,
            message="이미 체크아웃된 테이블 세션입니다.",
        )

    await db.commit()
    return table_session
