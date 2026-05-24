import uuid

from fastapi import Query
from pydantic import BaseModel

from app.schemas.common_schema import OffsetPaginatedResponse
from app.schemas.menu_price_schema import PriceResponse


class MenuResponse(BaseModel):
    id: uuid.UUID
    name: str
    name_en: str
    description: str
    taste_note: str
    abv: float
    tags: list[str]
    is_signature: bool
    is_display: bool
    prices: list[PriceResponse]


class MenuResponseForRecipe(BaseModel):
    id: uuid.UUID
    name: str
    name_en: str


class MenuOffsetFilterData(BaseModel):
    offset: int = Query(default=0, ge=0)
    limit: int = Query(default=20, ge=1, le=100)


MenuOffsetResponse = OffsetPaginatedResponse[MenuResponse]
