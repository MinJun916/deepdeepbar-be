import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth_dependency import require_admin
from app.models.user_model import User
from app.schemas.order_schema import (
    CreateOrderRequest,
    OrderFilterData,
    OrderPaginatedResponse,
    OrderResponse,
)
from app.services.order_service import (
    create_order,
    get_current_table_orders,
    get_order,
    get_orders,
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


@router.get("/", response_model=OrderPaginatedResponse)
async def read_orders(
    current_user: authorized_admin,
    db: db,
    filter_data: Annotated[OrderFilterData, Depends()],
):
    return await get_orders(db, filter_data)


@router.get("/{order_id}", response_model=OrderResponse)
async def read_order(
    order_id: uuid.UUID,
    current_user: authorized_admin,
    db: db,
):
    return await get_order(db, order_id)
