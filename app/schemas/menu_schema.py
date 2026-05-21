import uuid

from pydantic import BaseModel

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
