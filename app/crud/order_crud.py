import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload, with_loader_criteria

from app.constants.status_code import (
    CONFLICT,
    INTERNAL_SERVER_ERROR,
    NOT_FOUND,
    UNAUTHORIZED,
)
from app.core.exceptions import AppError
from app.crud.common.pagination_crud import apply_pagination
from app.models.base_model import get_utc_now
from app.models.menu_model import Menu
from app.models.menu_price_model import MenuPrice
from app.models.order_item_model import OrderItem
from app.models.order_model import Order
from app.models.table_session_model import TableSession
from app.schemas.order_schema import CreateOrderItemRequest, OrderFilterData


async def find_locked_active_table_session_crud(
    db: AsyncSession,
    token_hash: str,
) -> TableSession:
    result = await db.execute(
        select(TableSession)
        .where(
            TableSession.token_hash == token_hash,
            TableSession.checked_out_at.is_(None),
        )
        .with_for_update()
    )
    table_session = result.scalar_one_or_none()

    if table_session is None:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="유효한 테이블 세션을 찾을 수 없습니다.",
        )

    return table_session


async def find_order_by_idempotency_key_crud(
    db: AsyncSession,
    table_session_id: uuid.UUID,
    idempotency_key: uuid.UUID,
) -> Order | None:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(
            Order.table_session_id == table_session_id,
            Order.idempotency_key == idempotency_key,
        )
    )
    return result.scalar_one_or_none()


async def find_order_by_id_crud(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> Order | None:
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    return result.scalar_one_or_none()


async def find_orders_by_table_session_crud(
    db: AsyncSession,
    table_session_id: uuid.UUID,
) -> list[Order]:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(
            Order.table_session_id == table_session_id,
            Order.deleted_at.is_(None),
        )
        .order_by(Order.created_at.asc())
    )
    return list(result.scalars().all())


async def find_order_history_crud(
    db: AsyncSession,
    filter_data: OrderFilterData,
):
    query = (
        select(Order)
        .join(Order.table_session)
        .options(selectinload(Order.items))
        .where(
            Order.deleted_at.is_(None),
            TableSession.deleted_at.is_(None),
            TableSession.checked_out_at.is_not(None),
        )
    )

    if filter_data.table_number is not None:
        query = query.where(Order.table_number == filter_data.table_number)

    if filter_data.is_pos_registered is not None:
        query = query.where(Order.is_pos_registered.is_(filter_data.is_pos_registered))

    if filter_data.created_from is not None:
        query = query.where(Order.created_at >= filter_data.created_from)

    if filter_data.created_to is not None:
        query = query.where(Order.created_at <= filter_data.created_to)

    query = query.order_by(Order.created_at.desc())

    return await apply_pagination(
        db,
        query,
        filter_data.page,
        filter_data.limit,
    )


async def find_active_table_sessions_with_orders_crud(
    db: AsyncSession,
) -> list[TableSession]:
    result = await db.execute(
        select(TableSession)
        .options(
            selectinload(TableSession.orders).selectinload(Order.items),
            with_loader_criteria(Order, Order.deleted_at.is_(None)),
        )
        .where(
            TableSession.checked_out_at.is_(None),
            TableSession.deleted_at.is_(None),
        )
        .order_by(TableSession.table_number.asc())
    )
    return list(result.scalars().all())


async def update_order_pos_registration_crud(
    db: AsyncSession,
    order_id: uuid.UUID,
    is_pos_registered: bool,
) -> Order:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(
            Order.id == order_id,
            Order.deleted_at.is_(None),
        )
        .with_for_update()
    )
    order = result.scalar_one_or_none()

    if order is None:
        raise AppError(
            status_code=NOT_FOUND,
            message="주문을 찾을 수 없습니다.",
        )

    if order.is_pos_registered == is_pos_registered:
        await db.commit()
        return order

    changed_at = get_utc_now()
    order.is_pos_registered = is_pos_registered
    order.pos_registered_at = changed_at if is_pos_registered else None
    order.updated_at = changed_at

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return order


async def find_locked_orderable_menu_prices_crud(
    db: AsyncSession,
    menu_price_ids: list[uuid.UUID],
) -> dict[uuid.UUID, MenuPrice]:
    result = await db.execute(
        select(MenuPrice)
        .join(MenuPrice.menu)
        .options(contains_eager(MenuPrice.menu))
        .where(
            MenuPrice.id.in_(menu_price_ids),
            MenuPrice.is_active.is_(True),
            MenuPrice.deleted_at.is_(None),
            Menu.is_display.is_(True),
            Menu.is_sold_out.is_(False),
            Menu.deleted_at.is_(None),
        )
        .with_for_update()
    )
    menu_prices = result.scalars().all()
    return {menu_price.id: menu_price for menu_price in menu_prices}


async def create_order_crud(
    db: AsyncSession,
    table_session: TableSession,
    idempotency_key: uuid.UUID,
    request_hash: str,
    requested_items: list[CreateOrderItemRequest],
    menu_prices: dict[uuid.UUID, MenuPrice],
) -> Order:
    total_amount = sum(
        menu_prices[item.menu_price_id].price * item.quantity
        for item in requested_items
    )

    order = Order(
        table_session_id=table_session.id,
        table_number=table_session.table_number,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        total_amount=total_amount,
    )

    try:
        db.add(order)
        await db.flush()

        order_items = []

        for display_order, requested_item in enumerate(requested_items, start=1):
            menu_price = menu_prices[requested_item.menu_price_id]
            unit_price = menu_price.price

            order_items.append(
                OrderItem(
                    order_id=order.id,
                    menu_id=menu_price.menu_id,
                    menu_price_id=menu_price.id,
                    menu_name=menu_price.menu.name,
                    menu_name_en=menu_price.menu.name_en,
                    price_type=menu_price.price_type.value,
                    unit_price=unit_price,
                    quantity=requested_item.quantity,
                    line_total=unit_price * requested_item.quantity,
                    display_order=display_order,
                )
            )

        db.add_all(order_items)
        await db.commit()

    except IntegrityError:
        await db.rollback()

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

        raise AppError(
            status_code=INTERNAL_SERVER_ERROR,
            message=("주문 저장 중 데이터 정합성 오류가 발생했습니다."),
        )

    except Exception:
        await db.rollback()
        raise

    created_order = await find_order_by_id_crud(db, order.id)

    if created_order is None:
        raise AppError(
            status_code=INTERNAL_SERVER_ERROR,
            message="생성된 주문을 조회할 수 없습니다.",
        )

    return created_order
