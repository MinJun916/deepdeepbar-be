from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.glass_type_model import GlassType
from app.schemas.glass_type_schema import GlassTypeEnum


async def find_glass_type_id_by_code_crud(db: AsyncSession, code: GlassTypeEnum):
    result = await db.execute(select(GlassType.id).where(GlassType.code == code))
    return result.scalar_one_or_none()
