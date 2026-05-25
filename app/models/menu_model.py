from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.menu_price_model import MenuPrice
    from app.models.recipe_model import Recipe


class MenuCategoryEnum(StrEnum):
    cocktail = "cocktail"
    whisky = "whisky"
    non_alcohol = "non-alcohol"
    highball = "highball"
    beer = "beer"
    side = "side"


class Menu(BaseModel):
    __tablename__ = "menus"

    category: Mapped[MenuCategoryEnum] = mapped_column(
        Enum(
            MenuCategoryEnum,
            name="menu_category_enum",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    taste_note: Mapped[str] = mapped_column(Text, nullable=False)

    abv: Mapped[float] = mapped_column(Numeric, nullable=False)

    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    is_signature: Mapped[bool] = mapped_column(Boolean, nullable=False)

    is_display: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    is_sold_out: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    recipe: Mapped["Recipe | None"] = relationship(
        back_populates="menu",
        cascade="all, delete-orphan",
        uselist=False,
    )

    prices: Mapped[list["MenuPrice"]] = relationship(
        back_populates="menu",
        order_by="MenuPrice.display_order",
        cascade="all, delete-orphan",
    )
