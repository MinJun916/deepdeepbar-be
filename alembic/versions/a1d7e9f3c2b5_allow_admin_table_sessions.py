"""Allow administrator sessions and orders without a table number.

Revision ID: a1d7e9f3c2b5
Revises: a7e4c9d2f1b6
"""

import sqlalchemy as sa

from alembic import op

revision = "a1d7e9f3c2b5"
down_revision = "a7e4c9d2f1b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("table_sessions", "orders"):
        op.alter_column(
            table, "table_number", existing_type=sa.Integer(), nullable=True
        )


def downgrade() -> None:
    # Refuse rollback with admin data rather than delete it or invent table numbers.
    for table in ("orders", "table_sessions"):
        op.alter_column(
            table, "table_number", existing_type=sa.Integer(), nullable=False
        )
