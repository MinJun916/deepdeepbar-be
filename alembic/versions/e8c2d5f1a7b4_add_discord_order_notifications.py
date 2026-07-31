"""add discord order notifications

Revision ID: e8c2d5f1a7b4
Revises: d4f7a1c8e2b5
Create Date: 2026-07-31 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e8c2d5f1a7b4"
down_revision: Union[str, Sequence[str], None] = "d4f7a1c8e2b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "discord_order_notifications",
        sa.Column("order_id", sa.UUID(), nullable=False),
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
            name="ck_discord_order_notifications_attempt_count",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sending', 'sent', 'failed')",
            name="ck_discord_order_notifications_status",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )
    op.create_index(
        "ix_discord_order_notifications_status_attempted_at",
        "discord_order_notifications",
        ["status", "last_attempted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_discord_order_notifications_status_attempted_at",
        table_name="discord_order_notifications",
    )
    op.drop_table("discord_order_notifications")
