"""add table sessions

Revision ID: a4c3d2e1f0b9
Revises: 05d5af6b3131
Create Date: 2026-07-31 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4c3d2e1f0b9"
down_revision: Union[str, Sequence[str], None] = "05d5af6b3131"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "table_sessions",
        sa.Column("table_number", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("checked_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_out_by_user_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["checked_out_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "uq_active_table_session_table_number",
        "table_sessions",
        ["table_number"],
        unique=True,
        postgresql_where=sa.text("checked_out_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_active_table_session_table_number", table_name="table_sessions")
    op.drop_table("table_sessions")
