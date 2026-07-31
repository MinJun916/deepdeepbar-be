import uuid
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants.status_code import INTERNAL_SERVER_ERROR, NOT_FOUND
from app.core.exceptions import AppError
from app.crud.queries.menu_query import get_displayed_menu_query
from app.models.menu_model import Menu
from app.models.menu_price_model import MenuPrice
from app.schemas.menu_schema import (
    CreateMenuRequest,
    UpdateMenuRequest,
)

MENU_ORDER_BY = (
    desc(Menu.is_signature),
    Menu.name.asc(),
)


async def find_menu_by_id_crud(
    db: AsyncSession,
    menu_id: uuid.UUID,
):
    result = await db.execute(select(Menu).where(Menu.id == menu_id))
    return result.scalar_one_or_none()


# async def find_displayed_menus_with_offset(
#     db: AsyncSession,
#     filter_data: MenuOffsetFilterData,
# ):
#     query = (
#         get_displayed_menu_query()
#         .options(selectinload(Menu.prices))
#         .order_by(*MENU_ORDER_BY)
#     )

#     return await apply_offset_pagination(
#         db=db,
#         query=query,
#         offset=filter_data.offset,
#         limit=filter_data.limit,
#     )


async def find_displayed_menus_crud(
    db: AsyncSession,
):
    query = (
        get_displayed_menu_query()
        .options(selectinload(Menu.prices))
        .order_by(*MENU_ORDER_BY)
    )

    result = await db.execute(query)
    return result.scalars().all()


async def find_menu_by_id_with_prices(
    db: AsyncSession,
    menu_id,
):
    result = await db.execute(
        select(Menu).options(selectinload(Menu.prices)).where(Menu.id == menu_id)
    )

    return result.scalar_one_or_none()


async def create_menu_crud(
    db: AsyncSession,
    menu_data: CreateMenuRequest,
):
    try:
        menu = Menu(
            category=menu_data.category,
            name=menu_data.name,
            name_en=menu_data.name_en,
            description=menu_data.description,
            taste_note=menu_data.taste_note,
            abv=menu_data.abv,
            tags=menu_data.tags,
            is_signature=menu_data.is_signature,
            is_display=menu_data.is_display,
        )

        db.add(menu)

        await db.flush()

        prices = [
            MenuPrice(
                menu_id=menu.id,
                price_type=price_data.price_type,
                price=price_data.price,
                display_order=price_data.display_order,
                is_active=price_data.is_active,
            )
            for price_data in menu_data.prices
        ]

        db.add_all(prices)

        await db.commit()

        return await find_menu_by_id_with_prices(db, menu.id)

    except Exception as error:
        await db.rollback()
        raise AppError(status_code=INTERNAL_SERVER_ERROR, message=str(error))


async def update_menu_crud(
    db: AsyncSession,
    menu_id: uuid.UUID,
    menu_data: UpdateMenuRequest,
):
    try:
        menu = await find_menu_by_id_with_prices(db, menu_id)

        if menu is None:
            raise AppError(status_code=NOT_FOUND, message="메뉴를 찾을 수 없습니다.")

        update_data = menu_data.model_dump(
            exclude_unset=True,
            exclude={"prices"},
        )

        for key, value in update_data.items():
            setattr(menu, key, value)

        if menu_data.prices is not None:
            for price in menu.prices:
                await db.delete(price)

            await db.flush()

            new_prices = [
                MenuPrice(
                    menu_id=menu.id,
                    price_type=price_data.price_type,
                    price=price_data.price,
                    display_order=price_data.display_order,
                    is_active=price_data.is_active,
                )
                for price_data in menu_data.prices
            ]
            db.add_all(new_prices)

        await db.commit()
        db.expire(menu, ["prices"])

        return await find_menu_by_id_with_prices(db, menu.id)

    except AppError:
        raise

    except Exception as error:
        await db.rollback()
        raise AppError(status_code=INTERNAL_SERVER_ERROR, message=str(error))


async def soft_delete_menu_crud(
    db: AsyncSession,
    menu_id: uuid.UUID,
):
    menu = await find_menu_by_id_crud(db, menu_id)

    if menu is None:
        raise AppError(status_code=NOT_FOUND, message="메뉴를 찾을 수 없습니다.")

    menu.deleted_at = datetime.now()

    await db.commit()
    await db.refresh(menu)

    return {
        "id": menu.id,
        "deleted_at": menu.deleted_at,
        "message": "메뉴가 삭제되었습니다.",
    }
