from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="NILIFY_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Nilify API"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_prefix: str = "/api"
    host: str = "127.0.0.1"
    port: int = Field(default=5000, ge=1, le=65535)

    database_url: str
    database_echo: bool = False

    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_expire_minutes: int = Field(default=10080, ge=1)
    auth_cookie_name: str = "nilify_access_token"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    frontend_origins: str = "http://localhost:5173"

    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = Field(default=300, ge=10)
    scheduler_batch_size: int = Field(default=50, ge=1, le=500)
    scheduler_concurrency: int = Field(default=5, ge=1, le=20)

    scraper_timeout_seconds: float = Field(default=15.0, ge=1, le=60)
    scraper_max_bytes: int = Field(default=5_000_000, ge=10_000, le=20_000_000)
    scraper_max_redirects: int = Field(default=3, ge=0, le=10)
    scraper_user_agent: str = "NilifyPriceMonitor/1.0"

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
