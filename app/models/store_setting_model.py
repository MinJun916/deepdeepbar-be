from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel

GLOBAL_STORE_SCOPE = "global"


class StoreSetting(BaseModel):
    __tablename__ = "store_settings"

    scope: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        default=GLOBAL_STORE_SCOPE,
    )
    is_order_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )
