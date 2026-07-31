import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth_dependency import require_admin
from app.models.user_model import User
from app.schemas.discord_table_session_notification_schema import (
    DiscordTableSessionNotificationResponse,
)
from app.schemas.table_session_schema import (
    EnterTableRequest,
    EnterTableResponse,
    TableSessionResponse,
)
from app.services.discord_table_session_notification_service import (
    get_discord_table_session_notification,
    retry_discord_table_session_notification,
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
    summary="테이블 체크아웃",
    description=(
        "관리자가 결제 완료 테이블을 체크아웃합니다. 포스 미등록 주문이 남아 "
        "있으면 체크아웃할 수 없으며, 성공하면 Discord 체크인 메시지도 완료 "
        "상태로 갱신됩니다."
    ),
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


@router.get(
    "/{table_session_id}/discord-notification",
    response_model=DiscordTableSessionNotificationResponse,
    summary="Discord 체크인 알림 상태 조회",
)
async def read_discord_table_session_notification(
    table_session_id: uuid.UUID,
    current_user: authorized_admin,
    db: db,
):
    return await get_discord_table_session_notification(db, table_session_id)


@router.post(
    "/{table_session_id}/discord-notification/retry",
    response_model=DiscordTableSessionNotificationResponse,
    summary="Discord 체크인 알림 재전송",
    description=(
        "실패하거나 장시간 전송 중인 체크인 알림을 다시 전송합니다. 이미 전송된 "
        "알림과 현재 처리 중인 알림은 중복 전송하지 않습니다."
    ),
)
async def retry_table_session_discord_notification(
    table_session_id: uuid.UUID,
    current_user: authorized_admin,
    db: db,
):
    return await retry_discord_table_session_notification(db, table_session_id)
