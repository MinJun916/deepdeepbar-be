import hashlib
import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import BAD_REQUEST, CONFLICT, NOT_FOUND
from app.core.exceptions import AppError
from app.core.security import hash_token
from app.crud.order_crud import (
    create_order_crud,
    find_active_table_sessions_with_orders_crud,
    find_locked_active_table_session_crud,
    find_locked_orderable_menu_prices_crud,
    find_order_by_id_crud,
    find_order_by_idempotency_key_crud,
    find_order_history_crud,
    find_orders_by_table_session_crud,
    update_order_pos_registration_crud,
)
from app.crud.table_session_crud import find_active_table_session_by_token_hash_crud
from app.models.order_model import Order
from app.schemas.order_schema import (
    ActiveTableOrdersResponse,
    CreateOrderRequest,
    OrderFilterData,
)


def create_order_request_hash(order_data: CreateOrderRequest) -> str:
    normalized_items = sorted(
        (
            {
                "menu_price_id": str(item.menu_price_id),
                "quantity": item.quantity,
            }
            for item in order_data.items
        ),
        key=lambda item: item["menu_price_id"],
    )
    serialized_items = json.dumps(
        normalized_items,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized_items.encode()).hexdigest()


async def create_order(
    db: AsyncSession,
    session_token: str,
    idempotency_key: uuid.UUID,
    order_data: CreateOrderRequest,
) -> Order:
    table_session = await find_locked_active_table_session_crud(
        db,
        hash_token(session_token),
    )
    request_hash = create_order_request_hash(order_data)

    existing_order = await find_order_by_idempotency_key_crud(
        db,
        table_session.id,
        idempotency_key,
    )

    if existing_order is not None:
        if existing_order.request_hash != request_hash:
            raise AppError(
                status_code=CONFLICT,
                message=("동일한 Idempotency-Key가 다른 주문에 사용되었습니다."),
            )

        return existing_order

    menu_price_ids = [item.menu_price_id for item in order_data.items]
    menu_prices = await find_locked_orderable_menu_prices_crud(
        db,
        menu_price_ids,
    )

    if len(menu_prices) != len(menu_price_ids):
        raise AppError(
            status_code=BAD_REQUEST,
            message=("주문할 수 없는 메뉴 또는 가격이 포함되어 있습니다."),
        )

    if any(menu_price.price < 0 for menu_price in menu_prices.values()):
        raise AppError(
            status_code=BAD_REQUEST,
            message="올바르지 않은 메뉴 가격이 포함되어 있습니다.",
        )

    return await create_order_crud(
        db,
        table_session,
        idempotency_key,
        request_hash,
        order_data.items,
        menu_prices,
    )


async def get_current_table_orders(
    db: AsyncSession,
    session_token: str,
) -> list[Order]:
    table_session = await find_active_table_session_by_token_hash_crud(
        db,
        hash_token(session_token),
    )
    return await find_orders_by_table_session_crud(db, table_session.id)


async def get_order_history(
    db: AsyncSession,
    filter_data: OrderFilterData,
):
    return await find_order_history_crud(db, filter_data)


async def get_active_table_orders(
    db: AsyncSession,
) -> list[ActiveTableOrdersResponse]:
    table_sessions = await find_active_table_sessions_with_orders_crud(db)

    return [
        ActiveTableOrdersResponse(
            table_session_id=table_session.id,
            table_number=table_session.table_number,
            entered_at=table_session.created_at,
            order_count=len(table_session.orders),
            total_amount=sum(order.total_amount for order in table_session.orders),
            unregistered_order_count=sum(
                not order.is_pos_registered for order in table_session.orders
            ),
            orders=table_session.orders,
        )
        for table_session in table_sessions
    ]


async def update_order_pos_registration(
    db: AsyncSession,
    order_id: uuid.UUID,
    is_pos_registered: bool,
) -> Order:
    return await update_order_pos_registration_crud(
        db,
        order_id,
        is_pos_registered,
    )


async def get_order(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> Order:
    order = await find_order_by_id_crud(db, order_id)

    if order is None or order.deleted_at is not None:
        raise AppError(
            status_code=NOT_FOUND,
            message="주문을 찾을 수 없습니다.",
        )

    return order
