from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def apply_pagination(
    db: AsyncSession,
    query: Select,
    page: int,
    limit: int,
):
    offset = (page - 1) * limit

    count_query = select(func.count()).select_from(query.subquery())

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(query.offset(offset).limit(limit))

    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


async def apply_offset_pagination(
    db: AsyncSession,
    query: Select,
    offset: int,
    limit: int,
):
    result = await db.execute(query.offset(offset).limit(limit + 1))

    items = result.scalars().all()

    has_next = len(items) > limit
    sliced_items = items[:limit]

    next_offset = None

    if has_next:
        next_offset = offset + limit

    return {
        "items": sliced_items,
        "has_next": has_next,
        "next_offset": next_offset,
    }
