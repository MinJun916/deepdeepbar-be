import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import CONFLICT, NOT_FOUND, UNAUTHORIZED
from app.core.exceptions import AppError
from app.models.discord_table_session_notification_model import (
    DiscordTableSessionNotification,
)
from app.models.order_model import Order
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
        db.add(DiscordTableSessionNotification(table_session=table_session))
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppError(
            status_code=CONFLICT,
            message="현재 사용 중인 테이블 번호입니다.",
        )
    except Exception:
        await db.rollback()
        raise

    await db.refresh(table_session)
    return table_session


async def find_table_session_by_id_crud(
    db: AsyncSession,
    table_session_id: uuid.UUID,
) -> TableSession | None:
    result = await db.execute(
        select(TableSession).where(
            TableSession.id == table_session_id,
            TableSession.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


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
    checked_out_by_user_id: uuid.UUID | None,
    checked_out_by_discord_user_id: str | None,
    checked_out_at: datetime,
) -> TableSession:
    result = await db.execute(
        select(TableSession)
        .where(
            TableSession.id == table_session_id,
            TableSession.deleted_at.is_(None),
        )
        .with_for_update()
    )
    table_session = result.scalar_one_or_none()

    if table_session is None:
        raise AppError(
            status_code=NOT_FOUND,
            message="테이블 세션을 찾을 수 없습니다.",
        )

    if table_session.checked_out_at is not None:
        raise AppError(
            status_code=CONFLICT,
            message="이미 체크아웃된 테이블 세션입니다.",
        )

    unregistered_result = await db.execute(
        select(func.count(Order.id)).where(
            Order.table_session_id == table_session_id,
            Order.is_pos_registered.is_(False),
            Order.deleted_at.is_(None),
        )
    )
    unregistered_order_count = unregistered_result.scalar_one()

    if unregistered_order_count > 0:
        raise AppError(
            status_code=CONFLICT,
            message=(
                f"포스 미등록 주문이 {unregistered_order_count}건 남아 있어 "
                "체크아웃할 수 없습니다."
            ),
        )

    table_session.checked_out_at = checked_out_at
    table_session.checked_out_by_user_id = checked_out_by_user_id
    table_session.checked_out_by_discord_user_id = checked_out_by_discord_user_id
    table_session.updated_at = checked_out_at

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return table_session
