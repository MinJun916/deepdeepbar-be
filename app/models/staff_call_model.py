import uuid
from datetime import datetime, timedelta

from sqlalchemy import UUID, Boolean, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel, get_utc_now


class StaffCallOption(BaseModel):
    __tablename__ = "staff_call_options"

    label: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class StaffCall(BaseModel):
    __tablename__ = "staff_calls"
    __table_args__ = (
        Index(
            "uq_pending_staff_call",
            "table_session_id",
            "option_id",
            unique=True,
            postgresql_where=text("completed_at IS NULL"),
        ),
    )

    table_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("table_sessions.id")
    )
    option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_call_options.id")
    )
    table_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notification_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )
    discord_message_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivery_token: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    @property
    def retry_available(self) -> bool:
        if self.completed_at is not None:
            return False
        return self.notification_status in ("pending", "failed") or (
            self.notification_status == "sending"
            and (
                self.last_attempted_at is None
                or self.last_attempted_at <= get_utc_now() - timedelta(minutes=1)
            )
        )
