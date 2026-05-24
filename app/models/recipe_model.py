from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.glass_type_model import GlassType
    from app.models.menu_model import Menu
    from app.models.recipe_step_model import RecipeStep


class Recipe(BaseModel):
    __tablename__ = "recipes"

    menu_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    glass_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("glass_types.id"),
        nullable=False,
    )

    garnish: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    mixing_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    menu: Mapped["Menu"] = relationship(
        back_populates="recipe",
        order_by="Menu.name",
    )
    glass_type: Mapped["GlassType"] = relationship(back_populates="recipes")

    steps: Mapped[list["RecipeStep"]] = relationship(
        back_populates="recipe",
        order_by="RecipeStep.step_order",
        cascade="all, delete-orphan",
    )
