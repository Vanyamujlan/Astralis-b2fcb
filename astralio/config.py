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

    # Firebase / Firestore credentials (required for Firestore mode; optional in local preview mode)
    firebase_project_id: str | None = Field(default=None, alias="FIREBASE_PROJECT_ID")
    firebase_client_email: str | None = Field(default=None, alias="FIREBASE_CLIENT_EMAIL")
    firebase_private_key: SecretStr | None = Field(default=None, alias="FIREBASE_PRIVATE_KEY")
    firebase_database_id: str | None = Field(default=None, alias="FIREBASE_DATABASE_ID")

    # Storage backend: "auto" uses Firestore when Admin credentials are set, else local JSON file
    storage_mode: Literal["auto", "firestore", "local"] = Field(
        default="auto",
        alias="STORAGE_MODE",
    )
    local_db_path: str = Field(default=".astralio_local_db.json", alias="LOCAL_DB_PATH")

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

    @field_validator(
        "firebase_project_id", "firebase_client_email", "firebase_database_id", mode="before"
    )
    @classmethod
    def _empty_str_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip().strip('"').strip("'").strip()
        return stripped or None

    @field_validator("ai_api_key", "firebase_private_key", mode="before")
    @classmethod
    def _empty_secret_to_none(cls, value: str | SecretStr | None) -> str | SecretStr | None:
        if value is None:
            return None
        if isinstance(value, SecretStr):
            return value if value.get_secret_value().strip() else None
        stripped = str(value).strip()
        return stripped or None

    @field_validator("bot_token")
    @classmethod
    def _validate_bot_token(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value().strip().strip('"').strip("'").strip()
        if not raw or ":" not in raw:
            raise ValueError(
                "BOT_TOKEN must be a valid Telegram Bot API token (format '<id>:<hash>')."
            )
        return SecretStr(raw)

    @property
    def has_firebase_admin_credentials(self) -> bool:
        """Whether full Firebase Admin SDK service account credentials are configured."""
        return bool(
            self.firebase_project_id
            and self.firebase_client_email
            and self.firebase_private_key
            and self.firebase_private_key.get_secret_value().strip()
        )

    @property
    def resolved_storage_mode(self) -> Literal["firestore", "local"]:
        """Resolve effective storage backend based on STORAGE_MODE and credentials."""
        if self.storage_mode == "firestore":
            return "firestore"
        if self.storage_mode == "local":
            return "local"
        return "firestore" if self.has_firebase_admin_credentials else "local"

    @property
    def normalized_firebase_private_key(self) -> str:
        """Normalize Firebase private key pasted from .env or cloud Secrets UI."""
        if self.firebase_private_key is None:
            return ""
        import json
        import re

        raw = self.firebase_private_key.get_secret_value().strip()

        if raw.startswith("{"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and isinstance(parsed.get("private_key"), str):
                    raw = parsed["private_key"].strip()
            except Exception:
                pass

        # Convert escaped newlines (both \\n and \n) and CRLF into standard LF
        normalized = (
            raw.replace("\\\\n", "\n")
            .replace("\\n", "\n")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )

        # Always extract the clean PEM block (strips stray quotes, commas, JSON prefixes/suffixes)
        match = re.search(
            r"(-----BEGIN (?:RSA )?PRIVATE KEY-----)(.*?)(-----END (?:RSA )?PRIVATE KEY-----)",
            normalized,
            flags=re.DOTALL,
        )
        if match:
            begin_marker, body, end_marker = match.group(1), match.group(2), match.group(3)
            compact_body = "".join(body.split())
            lines = [compact_body[i : i + 64] for i in range(0, len(compact_body), 64)]
            return f"{begin_marker}\n" + "\n".join(lines) + f"\n{end_marker}\n"

        if (normalized.startswith('"') and normalized.endswith('"')) or (
            normalized.startswith("'") and normalized.endswith("'")
        ):
            normalized = normalized[1:-1].strip()
        if normalized and not normalized.endswith("\n"):
            normalized += "\n"
        return normalized

    @property
    def has_ai_configured(self) -> bool:
        """Whether an external AI API key is configured."""
        return self.ai_api_key is not None and bool(self.ai_api_key.get_secret_value().strip())

    def secret_values(self) -> list[str]:
        """Return all configured secret strings for log redaction."""
        secrets: list[str] = [self.bot_token.get_secret_value()]
        if self.firebase_private_key is not None:
            secrets.append(self.firebase_private_key.get_secret_value())
            secrets.append(self.normalized_firebase_private_key)
        if self.ai_api_key is not None:
            secrets.append(self.ai_api_key.get_secret_value())
        return [s for s in secrets if s]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache Settings from environment."""
    return Settings()  # type: ignore[call-arg]
