import uuid

from pydantic import BaseModel


class GlassTypeResponse(BaseModel):
    id: uuid.UUID
    code: str
    name_ko: str
    name_en: str | None
    description: str | None
