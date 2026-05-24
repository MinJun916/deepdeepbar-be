import uuid
from enum import StrEnum

from pydantic import BaseModel


class GlassTypeEnum(StrEnum):
    double_shot_glass = "double_shot_glass"
    highball_glass = "highball_glass"
    hurricane_glass = "hurricane_glass"
    long_drink_glass = "long_drink_glass"
    margarita_glass = "margarita_glass"
    martini_glass = "martini_glass"
    old_fashioned_glass = "old_fashioned_glass"
    rocks_glass = "rocks_glass"
    shot_glass = "shot_glass"


class GlassTypeResponse(BaseModel):
    id: uuid.UUID
    code: GlassTypeEnum
    name_ko: str
    name_en: str | None
    description: str | None
