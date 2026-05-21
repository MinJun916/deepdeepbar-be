from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.recipe_model import Recipe


class MenuCategoryEnum(StrEnum):
    COCKTAIL = "cocktail"
    WHISKY = "whisky"
    NON_ALCOHOL = "non-alcohol"
    HIGHBALL = "highball"
    SIDE = "side"


class Menu(BaseModel):
    __tablename__ = "menus"

    category: Mapped[MenuCategoryEnum] = mapped_column(
        Enum(MenuCategoryEnum), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    price: Mapped[int] = mapped_column(Integer, nullable=False)

    taste_note: Mapped[str] = mapped_column(Text, nullable=False)

    abv: Mapped[float] = mapped_column(Numeric, nullable=False)

    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    is_signature: Mapped[bool] = mapped_column(Boolean, nullable=False)

    recipe: Mapped["Recipe | None"] = relationship(
        back_populates="menu",
        cascade="all, delete-orphan",
        uselist=False,
    )
