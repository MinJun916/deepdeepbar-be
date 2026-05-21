from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.recipe_model import Recipe


class RecipeStep(BaseModel):
    __tablename__ = "recipe_steps"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )

    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    instruction: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    recipe: Mapped["Recipe"] = relationship(back_populates="steps")
