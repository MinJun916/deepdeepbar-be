import uuid

from fastapi import Query
from pydantic import BaseModel

from app.models.menu_model import MenuCategoryEnum
from app.schemas.common_schema import OffsetPaginatedResponse
from app.schemas.menu_price_schema import (
    CreatePriceRequest,
    PriceResponse,
    UpdatePriceRequest,
)


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
    is_sold_out: bool
    prices: list[PriceResponse]


class MenuResponseForRecipe(BaseModel):
    id: uuid.UUID
    name: str
    name_en: str


class MenuOffsetFilterData(BaseModel):
    offset: int = Query(default=0, ge=0)
    limit: int = Query(default=20, ge=1, le=100)


MenuOffsetResponse = OffsetPaginatedResponse[MenuResponse]


class CreateMenuRequest(BaseModel):
    category: MenuCategoryEnum
    name: str
    name_en: str
    description: str
    taste_note: str
    abv: float
    tags: list[str]
    is_signature: bool
    is_display: bool
    prices: list[CreatePriceRequest]


class UpdateMenuRequest(BaseModel):
    category: MenuCategoryEnum | None = None
    name: str | None = None
    name_en: str | None = None
    description: str | None = None
    taste_note: str | None = None
    abv: float | None = None
    tags: list[str] | None = None
    is_signature: bool | None = None
    is_display: bool | None = None
    prices: list[UpdatePriceRequest] | None = None
