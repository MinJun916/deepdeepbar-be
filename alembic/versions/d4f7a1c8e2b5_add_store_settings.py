"""add store settings

Revision ID: d4f7a1c8e2b5
Revises: c9a6f3e2d8b1
Create Date: 2026-07-31 00:00:00.000000

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4f7a1c8e2b5"
down_revision: Union[str, Sequence[str], None] = "c9a6f3e2d8b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GLOBAL_STORE_SETTING_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def upgrade() -> None:
    op.create_table(
        "store_settings",
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column(
            "is_order_enabled",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scope"),
    )

    store_settings = sa.table(
        "store_settings",
        sa.column("id", sa.UUID()),
        sa.column("scope", sa.String()),
    )
    op.bulk_insert(
        store_settings,
        [
            {
                "id": GLOBAL_STORE_SETTING_ID,
                "scope": "global",
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("store_settings")
