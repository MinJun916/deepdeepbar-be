from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UpdateOrderModeRequest(BaseModel):
    is_order_enabled: bool


class OrderModeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_order_enabled: bool
    updated_at: datetime
