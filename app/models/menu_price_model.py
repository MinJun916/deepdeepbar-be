from __future__ import annotations

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.menu_model import Menu


class PriceTypeEnum(StrEnum):
    bottle = "bottle"
    shot = "shot"
    default = "default"


class MenuPrice(BaseModel):
    __tablename__ = "menu_prices"

    __table_args__ = (
        UniqueConstraint(
            "menu_id",
            "price_type",
            name="uq_menu_prices_menu_id_price_type",
        ),
    )

    menu_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=False,
    )

    price_type: Mapped[PriceTypeEnum] = mapped_column(
        Enum(
            PriceTypeEnum,
            name="price_type_enum",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=PriceTypeEnum.default,
    )

    price: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    menu: Mapped["Menu"] = relationship(back_populates="prices")
