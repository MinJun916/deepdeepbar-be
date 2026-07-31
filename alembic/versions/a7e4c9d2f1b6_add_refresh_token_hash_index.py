"""add refresh token hash index

Revision ID: a7e4c9d2f1b6
Revises: f3b8c1d6e4a2
Create Date: 2026-07-31 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "a7e4c9d2f1b6"
down_revision: Union[str, Sequence[str], None] = "f3b8c1d6e4a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_refresh_tokens_token_hash",
        "refresh_tokens",
        ["token_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_refresh_tokens_token_hash",
        table_name="refresh_tokens",
    )
