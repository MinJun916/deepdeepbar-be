import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.discord_order_notification_model import DiscordNotificationStatus


class DiscordOrderNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    status: DiscordNotificationStatus
    attempt_count: int
    last_attempted_at: datetime | None
    sent_at: datetime | None
    discord_message_id: str | None
    last_error: str | None
