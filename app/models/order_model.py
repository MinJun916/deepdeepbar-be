from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.discord_order_notification_model import DiscordOrderNotification
    from app.models.order_item_model import OrderItem
    from app.models.table_session_model import TableSession


class Order(BaseModel):
    __tablename__ = "orders"

    __table_args__ = (
        UniqueConstraint(
            "table_session_id",
            "idempotency_key",
            name="uq_orders_table_session_idempotency_key",
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="ck_orders_total_amount_non_negative",
        ),
        Index(
            "ix_orders_table_session_created_at",
            "table_session_id",
            "created_at",
        ),
        Index(
            "ix_orders_table_number_created_at",
            "table_number",
            "created_at",
        ),
        Index(
            "ix_orders_pos_created_at",
            "is_pos_registered",
            "created_at",
        ),
    )

    table_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("table_sessions.id"),
        nullable=False,
    )
    table_number: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_pos_registered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    pos_registered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    table_session: Mapped["TableSession"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        order_by="OrderItem.display_order",
        cascade="all, delete-orphan",
    )
    discord_notification: Mapped["DiscordOrderNotification | None"] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        uselist=False,
    )
