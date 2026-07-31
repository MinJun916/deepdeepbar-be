import uuid
from datetime import datetime

from fastapi import Query
from pydantic import AwareDatetime, BaseModel, Field, model_validator

from app.models.menu_price_model import PriceTypeEnum
from app.schemas.common_schema import PaginatedResponse


class CreateOrderItemRequest(BaseModel):
    menu_price_id: uuid.UUID
    quantity: int = Field(ge=1, le=99)


class CreateOrderRequest(BaseModel):
    items: list[CreateOrderItemRequest] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_unique_menu_prices(self):
        menu_price_ids = [item.menu_price_id for item in self.items]

        if len(menu_price_ids) != len(set(menu_price_ids)):
            raise ValueError(
                "동일한 메뉴 가격을 중복해서 주문할 수 없습니다."
            )

        return self


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    menu_id: uuid.UUID
    menu_price_id: uuid.UUID | None
    menu_name: str
    menu_name_en: str
    price_type: PriceTypeEnum
    unit_price: int
    quantity: int
    line_total: int
    display_order: int


class OrderResponse(BaseModel):
    id: uuid.UUID
    table_session_id: uuid.UUID
    table_number: int
    idempotency_key: uuid.UUID
    total_amount: int
    is_pos_registered: bool
    pos_registered_at: datetime | None
    created_at: datetime
    items: list[OrderItemResponse]


class OrderFilterData(BaseModel):
    table_number: int | None = Query(default=None, gt=0)
    is_pos_registered: bool | None = None
    created_from: AwareDatetime | None = None
    created_to: AwareDatetime | None = None
    page: int = Query(default=1, ge=1)
    limit: int = Query(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_created_date_range(self):
        if (
            self.created_from is not None
            and self.created_to is not None
            and self.created_from > self.created_to
        ):
            raise ValueError("조회 시작 시각은 종료 시각보다 늦을 수 없습니다.")

        return self


OrderPaginatedResponse = PaginatedResponse[OrderResponse]
