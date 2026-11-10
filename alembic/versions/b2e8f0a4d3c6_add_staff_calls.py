"""Add configurable staff calls.

Revision ID: b2e8f0a4d3c6
Revises: a1d7e9f3c2b5
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa

from alembic import op

revision = "b2e8f0a4d3c6"
down_revision = "a1d7e9f3c2b5"
branch_labels = None
depends_on = None


def base_columns():
    return [
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade():
    options = op.create_table(
        "staff_call_options",
        *base_columns(),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
    )
    op.create_table(
        "staff_calls",
        *base_columns(),
        sa.Column(
            "table_session_id",
            sa.UUID(),
            sa.ForeignKey("table_sessions.id"),
            nullable=False,
        ),
        sa.Column(
            "option_id",
            sa.UUID(),
            sa.ForeignKey("staff_call_options.id"),
            nullable=False,
        ),
        sa.Column("table_number", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notification_status", sa.String(20), nullable=False),
        sa.Column("discord_message_id", sa.String(30), nullable=True),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_token", sa.UUID(), nullable=True),
    )
    op.create_index(
        "uq_pending_staff_call",
        "staff_calls",
        ["table_session_id", "option_id"],
        unique=True,
        postgresql_where=sa.text("completed_at IS NULL"),
    )
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        options,
        [
            {
                "id": uuid.uuid4(),
                "created_at": now,
                "updated_at": now,
                "label": label,
                "is_active": True,
                "display_order": i,
            }
            for i, label in enumerate(
                ["💧 물 주세요!", "🪑 자리 바꾸고 싶어요!", "🥨 기본 안주 더 주세요!"]
            )
        ],
    )


def downgrade():
    op.drop_table("staff_calls")
    op.drop_table("staff_call_options")
