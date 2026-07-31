import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth_dependency import require_admin
from app.models.user_model import User
from app.schemas.order_schema import (
    ActiveTableOrdersResponse,
    CreateOrderRequest,
    OrderFilterData,
    OrderPaginatedResponse,
    OrderResponse,
    UpdateOrderPosRegistrationRequest,
)
from app.services.order_service import (
    create_order,
    get_active_table_orders,
    get_current_table_orders,
    get_order,
    get_order_history,
    update_order_pos_registration,
)

router = APIRouter(prefix="/orders", tags=["orders"])

db = Annotated[AsyncSession, Depends(get_db)]
authorized_admin = Annotated[User, Depends(require_admin)]
table_session_token = Annotated[
    str,
    Header(
        alias="X-Table-Session-Token",
        min_length=1,
        description="테이블 입장 시 발급받은 세션 토큰",
    ),
]
idempotency_key = Annotated[
    uuid.UUID,
    Header(
        alias="Idempotency-Key",
        description="주문 중복 생성을 방지하는 요청별 UUID",
    ),
]


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_order(
    order_data: CreateOrderRequest,
    session_token: table_session_token,
    request_idempotency_key: idempotency_key,
    db: db,
):
    return await create_order(
        db,
        session_token,
        request_idempotency_key,
        order_data,
    )


@router.get("/current", response_model=list[OrderResponse])
async def read_current_table_orders(
    session_token: table_session_token,
    db: db,
):
    return await get_current_table_orders(db, session_token)


@router.get(
    "/history",
    response_model=OrderPaginatedResponse,
    summary="체크아웃 완료 주문 이력 조회",
    description=(
        "조회 시점에 체크아웃이 완료된 테이블 세션의 주문만 최신 주문순으로 조회합니다."
    ),
)
async def read_order_history(
    current_user: authorized_admin,
    db: db,
    filter_data: Annotated[OrderFilterData, Depends()],
):
    return await get_order_history(db, filter_data)


@router.get(
    "/active-tables",
    response_model=list[ActiveTableOrdersResponse],
    summary="이용 중인 테이블별 주문 현황 조회",
    description=(
        "조회 시점에 체크아웃되지 않은 테이블을 테이블별로 구분하여 "
        "주문 목록과 누적 정보를 조회합니다. 주문이 없는 이용 중 테이블도 "
        "포함됩니다."
    ),
)
async def read_active_table_orders(
    current_user: authorized_admin,
    db: db,
):
    return await get_active_table_orders(db)


@router.patch(
    "/{order_id}/pos-registration",
    response_model=OrderResponse,
    summary="주문 포스 등록 상태 변경",
    description=(
        "관리자가 주문의 포스 등록 여부를 변경합니다. 등록 시각은 최초 등록 시 "
        "기록되고, 등록 취소 시 초기화됩니다. 동일 상태의 반복 요청은 기존 "
        "등록 시각을 유지합니다."
    ),
)
async def patch_order_pos_registration(
    order_id: uuid.UUID,
    pos_registration_data: UpdateOrderPosRegistrationRequest,
    current_user: authorized_admin,
    db: db,
):
    return await update_order_pos_registration(
        db,
        order_id,
        pos_registration_data.is_pos_registered,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def read_order(
    order_id: uuid.UUID,
    current_user: authorized_admin,
    db: db,
):
    return await get_order(db, order_id)
