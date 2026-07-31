from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
