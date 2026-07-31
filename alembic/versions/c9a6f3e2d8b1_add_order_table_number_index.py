"""add order table number index

Revision ID: c9a6f3e2d8b1
Revises: b7d4e9f2a1c6
Create Date: 2026-07-31 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9a6f3e2d8b1"
down_revision: Union[str, Sequence[str], None] = "b7d4e9f2a1c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_orders_table_number_created_at",
        "orders",
        ["table_number", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_orders_table_number_created_at", table_name="orders")
