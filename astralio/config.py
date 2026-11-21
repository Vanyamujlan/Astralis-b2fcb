"""Application settings loaded strictly from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration for Astralio Telegram Bot."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Required Telegram Bot token
    bot_token: SecretStr = Field(alias="BOT_TOKEN")

    # Required Firebase / Firestore credentials
    firebase_project_id: str = Field(alias="FIREBASE_PROJECT_ID", min_length=1)
    firebase_client_email: str = Field(alias="FIREBASE_CLIENT_EMAIL", min_length=3)
    firebase_private_key: SecretStr = Field(alias="FIREBASE_PRIVATE_KEY")
    firebase_database_id: str | None = Field(default=None, alias="FIREBASE_DATABASE_ID")

    # Optional AI interpretation service (fallback to local deterministic engine when empty)
    ai_api_key: SecretStr | None = Field(default=None, alias="AI_API_KEY")
    ai_base_url: str = Field(default="https://api.openai.com/v1", alias="AI_BASE_URL")
    ai_model: str = Field(default="gpt-4o-mini", alias="AI_MODEL")
    ai_timeout_seconds: float = Field(default=15.0, ge=1.0, le=60.0, alias="AI_TIMEOUT_SECONDS")
    ai_rate_limit_per_minute: int = Field(
        default=5,
        ge=1,
        le=60,
        alias="AI_RATE_LIMIT_PER_MINUTE",
    )

    # Optional Telegram Stars feature flag (must never simulate payments)
    telegram_stars_enabled: bool = Field(default=False, alias="TELEGRAM_STARS_ENABLED")

    # Geocoding & runtime
    geocoding_enabled: bool = Field(default=True, alias="GEOCODING_ENABLED")
    geocoding_timeout_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        alias="GEOCODING_TIMEOUT_SECONDS",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    @field_validator("firebase_database_id", mode="before")
    @classmethod
    def _empty_str_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @field_validator("ai_api_key", mode="before")
    @classmethod
    def _empty_ai_key_to_none(cls, value: str | SecretStr | None) -> str | SecretStr | None:
        if value is None:
            return None
        if isinstance(value, SecretStr):
            return value if value.get_secret_value().strip() else None
        stripped = str(value).strip()
        return stripped or None

    @field_validator("bot_token")
    @classmethod
    def _validate_bot_token(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value().strip()
        if not raw or ":" not in raw:
            raise ValueError(
                "BOT_TOKEN must be a valid Telegram Bot API token (format '<id>:<hash>')."
            )
        return SecretStr(raw)

    @field_validator("firebase_private_key")
    @classmethod
    def _validate_private_key(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value().strip()
        if not raw:
            raise ValueError("FIREBASE_PRIVATE_KEY must not be empty.")
        return SecretStr(raw)

    @property
    def normalized_firebase_private_key(self) -> str:
        """Return Firebase private key with escaped newlines converted to real newlines."""
        return self.firebase_private_key.get_secret_value().replace("\\n", "\n")

    @property
    def has_ai_configured(self) -> bool:
        """Whether an external AI API key is configured."""
        return self.ai_api_key is not None and bool(self.ai_api_key.get_secret_value().strip())

    def secret_values(self) -> list[str]:
        """Return all configured secret strings for log redaction."""
        secrets: list[str] = [
            self.bot_token.get_secret_value(),
            self.firebase_private_key.get_secret_value(),
            self.normalized_firebase_private_key,
        ]
        if self.ai_api_key is not None:
            secrets.append(self.ai_api_key.get_secret_value())
        return [s for s in secrets if s]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache Settings from environment."""
    return Settings()  # type: ignore[call-arg]
