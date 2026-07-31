from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.order_model import Order


class DiscordNotificationStatus(StrEnum):
    pending = "pending"
    sending = "sending"
    sent = "sent"
    failed = "failed"


class DiscordOrderNotification(BaseModel):
    __tablename__ = "discord_order_notifications"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'sending', 'sent', 'failed')",
            name="ck_discord_order_notifications_status",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_discord_order_notifications_attempt_count",
        ),
        Index(
            "ix_discord_order_notifications_status_attempted_at",
            "status",
            "last_attempted_at",
        ),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[DiscordNotificationStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DiscordNotificationStatus.pending,
        server_default=text("'pending'"),
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    discord_message_id: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    last_error: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    delivery_token: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    order: Mapped["Order"] = relationship(back_populates="discord_notification")
