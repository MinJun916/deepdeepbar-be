import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.discord_order_notification_model import DiscordNotificationStatus


class DiscordTableSessionNotificationResponse(BaseModel):
    id: uuid.UUID
    table_session_id: uuid.UUID
    status: DiscordNotificationStatus
    attempt_count: int
    last_attempted_at: datetime | None
    sent_at: datetime | None
    discord_message_id: str | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
