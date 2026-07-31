"""add discord table session notifications

Revision ID: f3b8c1d6e4a2
Revises: e8c2d5f1a7b4
Create Date: 2026-07-31 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "f3b8c1d6e4a2"
down_revision: Union[str, Sequence[str], None] = "e8c2d5f1a7b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "table_sessions",
        sa.Column(
            "checked_out_by_discord_user_id",
            sa.String(length=30),
            nullable=True,
        ),
    )
    op.create_table(
        "discord_table_session_notifications",
        sa.Column("table_session_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discord_message_id", sa.String(length=30), nullable=True),
        sa.Column("last_error", sa.String(length=1000), nullable=True),
        sa.Column("delivery_token", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="ck_discord_table_session_notifications_attempt_count",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sending', 'sent', 'failed')",
            name="ck_discord_table_session_notifications_status",
        ),
        sa.ForeignKeyConstraint(
            ["table_session_id"],
            ["table_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("table_session_id"),
    )
    op.create_index(
        "ix_discord_table_session_notifications_status_attempted_at",
        "discord_table_session_notifications",
        ["status", "last_attempted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_discord_table_session_notifications_status_attempted_at",
        table_name="discord_table_session_notifications",
    )
    op.drop_table("discord_table_session_notifications")
    op.drop_column("table_sessions", "checked_out_by_discord_user_id")
