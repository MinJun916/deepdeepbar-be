from sqlalchemy import JSONB, Boolean, Enum, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel
from app.schemas.menu_schema import MenuCategoryEnum


class Menu(BaseModel):
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
