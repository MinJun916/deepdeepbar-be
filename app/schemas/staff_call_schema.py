import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StaffCallOptionRequest(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    is_active: bool = True
    display_order: int = Field(default=0, ge=0, le=999)

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("호출 내용을 입력해주세요.")
        return value


class StaffCallOptionResponse(StaffCallOptionRequest):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class CreateStaffCallRequest(BaseModel):
    option_id: uuid.UUID


class StaffCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    option_id: uuid.UUID
    label: str
    table_number: int | None
    created_at: datetime
    completed_at: datetime | None
    notification_status: Literal["pending", "sending", "sent", "failed"]
    retry_available: bool
