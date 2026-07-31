import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EnterTableRequest(BaseModel):
    table_number: int = Field(gt=0)


class TableSessionResponse(BaseModel):
    id: uuid.UUID
    table_number: int
    created_at: datetime
    checked_out_at: datetime | None
    checked_out_by_user_id: uuid.UUID | None
    checked_out_by_discord_user_id: str | None
    is_active: bool


class EnterTableResponse(TableSessionResponse):
    session_token: str
