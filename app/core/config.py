from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    auth_refresh_cookie_secure: bool = True
    auth_refresh_cookie_samesite: Literal["lax", "strict", "none"] = "none"
    auth_refresh_cookie_domain: str | None = None

    discord_api_timeout_seconds: float = Field(
        default=5.0,
        gt=0,
        le=30,
    )
    # 기존 배포 환경의 Webhook 설정을 무시하지 않고 안전하게 흡수한다.
    discord_order_webhook_url: str | None = None
    discord_order_webhook_timeout_seconds: float | None = Field(
        default=None,
        gt=0,
        le=30,
    )
    discord_application_id: str | None = None
    discord_public_key: SecretStr | None = None
    discord_bot_token: SecretStr | None = None
    discord_guild_id: str | None = None
    discord_order_channel_id: str | None = None
    discord_table_channel_id: str | None = None

    @property
    def discord_timeout_seconds(self) -> float:
        return (
            self.discord_order_webhook_timeout_seconds
            or self.discord_api_timeout_seconds
        )

    @property
    def refresh_cookie_max_age_seconds(self) -> int:
        return 60 * 60 * 24 * self.refresh_token_expire_days

    @field_validator("auth_refresh_cookie_domain", mode="before")
    @classmethod
    def normalize_empty_cookie_domain(cls, value):
        return value or None

    @model_validator(mode="after")
    def validate_refresh_cookie_security(self):
        if (
            self.auth_refresh_cookie_samesite == "none"
            and not self.auth_refresh_cookie_secure
        ):
            raise ValueError("SameSite=None refresh cookie는 Secure=true가 필요합니다.")

        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
