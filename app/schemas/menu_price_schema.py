import uuid

from pydantic import BaseModel

from app.models.menu_price_model import PriceTypeEnum


class PriceResponse(BaseModel):
    id: uuid.UUID
    menu_id: uuid.UUID
    price_type: PriceTypeEnum
    price: int
    display_order: int


class CreatePriceRequest(BaseModel):
    price_type: PriceTypeEnum
    price: int
    display_order: int
    is_active: bool = True


class UpdatePriceRequest(BaseModel):
    price_type: PriceTypeEnum
    price: int
    display_order: int
    is_active: bool
