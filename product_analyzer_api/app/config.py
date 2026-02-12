from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Product Analyzer API"
    environment: str = Field(default="development")
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    vision_api_key: str = Field(..., alias="VISION_API_KEY")
    vision_api_url: str = Field(
        default="https://api.openai.com/v1/responses", alias="VISION_API_URL"
    )
    vision_model: str = Field(default="gpt-4.1-mini", alias="VISION_MODEL")
    request_timeout_seconds: float = Field(default=30.0, alias="REQUEST_TIMEOUT_SECONDS")

    cors_allow_origins: list[str] = Field(default=["*"], alias="CORS_ALLOW_ORIGINS")

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_allow_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return [item.strip().strip('"') for item in stripped.strip("[]").split(",") if item.strip()]
            return [item.strip() for item in value.split(",") if item.strip()]
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
