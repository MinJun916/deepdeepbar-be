from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int


class OffsetPaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    has_next: bool
    next_offset: int | None
