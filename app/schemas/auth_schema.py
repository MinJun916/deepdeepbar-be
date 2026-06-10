from pydantic import BaseModel

from app.models.user_model import UserRole


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class CreateAdminRequest(BaseModel):
    email: str
    password_hash: str
    name: str
    role: UserRole = UserRole.admin
    is_active: bool = True


class LogoutResponse(BaseModel):
    message: str
