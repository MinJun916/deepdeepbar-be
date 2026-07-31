"""add orders

Revision ID: b7d4e9f2a1c6
Revises: a4c3d2e1f0b9
Create Date: 2026-07-31 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d4e9f2a1c6"
down_revision: Union[str, Sequence[str], None] = "a4c3d2e1f0b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("table_session_id", sa.UUID(), nullable=False),
        sa.Column("table_number", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.UUID(), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("total_amount", sa.BigInteger(), nullable=False),
        sa.Column(
            "is_pos_registered",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("pos_registered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "total_amount >= 0",
            name="ck_orders_total_amount_non_negative",
        ),
        sa.ForeignKeyConstraint(["table_session_id"], ["table_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "table_session_id",
            "idempotency_key",
            name="uq_orders_table_session_idempotency_key",
        ),
    )
    op.create_index(
        "ix_orders_pos_created_at",
        "orders",
        ["is_pos_registered", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_orders_table_session_created_at",
        "orders",
        ["table_session_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "order_items",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("menu_id", sa.UUID(), nullable=False),
        sa.Column("menu_price_id", sa.UUID(), nullable=True),
        sa.Column("menu_name", sa.String(length=255), nullable=False),
        sa.Column("menu_name_en", sa.String(length=255), nullable=False),
        sa.Column("price_type", sa.String(length=20), nullable=False),
        sa.Column("unit_price", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total", sa.BigInteger(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "line_total >= 0",
            name="ck_order_items_line_total_non_negative",
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_order_items_quantity_positive",
        ),
        sa.CheckConstraint(
            "unit_price >= 0",
            name="ck_order_items_unit_price_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["menu_id"],
            ["menus.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["menu_price_id"],
            ["menu_prices.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_id",
            "menu_price_id",
            name="uq_order_items_order_menu_price",
        ),
    )
    op.create_index(
        "ix_order_items_order_id",
        "order_items",
        ["order_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("ix_orders_table_session_created_at", table_name="orders")
    op.drop_index("ix_orders_pos_created_at", table_name="orders")
    op.drop_table("orders")
