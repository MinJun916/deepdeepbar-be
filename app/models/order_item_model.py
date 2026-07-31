from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.menu_model import Menu
    from app.models.menu_price_model import MenuPrice
    from app.models.order_model import Order


class OrderItem(BaseModel):
    __tablename__ = "order_items"

    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "menu_price_id",
            name="uq_order_items_order_menu_price",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_order_items_unit_price_non_negative",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_order_items_quantity_positive",
        ),
        CheckConstraint(
            "line_total >= 0",
            name="ck_order_items_line_total_non_negative",
        ),
        Index("ix_order_items_order_id", "order_id"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    menu_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menus.id", ondelete="RESTRICT"),
        nullable=False,
    )
    menu_price_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menu_prices.id", ondelete="SET NULL"),
        nullable=True,
    )
    menu_name: Mapped[str] = mapped_column(String(255), nullable=False)
    menu_name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    price_type: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[int] = mapped_column(BigInteger, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    menu: Mapped["Menu"] = relationship()
    menu_price: Mapped["MenuPrice | None"] = relationship()
