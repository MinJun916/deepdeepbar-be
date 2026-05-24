import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.user_model import UserRole


class CreateUserRequest(BaseModel):
    email: str
    password: str
    name: str
    role: UserRole = UserRole.staff


class UpdateUserRequest(BaseModel):
    name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
