from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.recipe_model import Recipe


class GlassType(BaseModel):
    __tablename__ = "glass_types"

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    name_ko: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    name_en: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    recipes: Mapped[list["Recipe"]] = relationship(back_populates="glass_type")
