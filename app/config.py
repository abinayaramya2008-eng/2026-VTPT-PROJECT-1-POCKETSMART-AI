import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PocketSmart AI"
    app_env: str = "development"
    secret_key: str = "change-me"
    database_url: str = "sqlite:///./pocketsmart.db"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    mock_ai: bool = False
    max_image_mb: int = 5
    session_https_only: bool = False
    cors_origins: list[str] = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
    jwt_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Accept both CSV and JSON-list values from .env/configuration."""
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []

            # Accept: ["http://localhost:8000", "http://127.0.0.1:8000"]
            if raw.startswith("["):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass

            # Accept: http://localhost:8000,http://127.0.0.1:8000
            return [item.strip().strip('"\'') for item in raw.split(",") if item.strip()]

        return value

    @property
    def max_image_bytes(self) -> int:
        return self.max_image_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
