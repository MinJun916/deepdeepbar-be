from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class TableSession(BaseModel):
    __tablename__ = "table_sessions"

    __table_args__ = (
        Index(
            "uq_active_table_session_table_number",
            "table_number",
            unique=True,
            postgresql_where=text("checked_out_at IS NULL"),
        ),
    )

    table_number: Mapped[int] = mapped_column(Integer, nullable=False)
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )
    checked_out_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    checked_out_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    @property
    def is_active(self) -> bool:
        return self.checked_out_at is None
