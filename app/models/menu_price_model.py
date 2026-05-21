from __future__ import annotations

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, Enum, ForeignKey, Integer
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

    menu_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    price_type: Mapped[PriceTypeEnum] = mapped_column(
        Enum(PriceTypeEnum),
        nullable=False,
        default=PriceTypeEnum.default,
        unique=True,
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
