"""Structured logging with automatic secret redaction."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable

_TELEGRAM_TOKEN_RE = re.compile(r"\b\d{6,15}:[A-Za-z0-9_-]{20,}\b")
_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)
_BEARER_RE = re.compile(r"(Bearer\s+)[A-Za-z0-9._\-]+", re.IGNORECASE)


class SecretRedactionFilter(logging.Filter):
    """Logging filter that strips known secrets and sensitive token patterns."""

    def __init__(self, secrets: Iterable[str] = ()) -> None:
        super().__init__()
        self._secrets = [s for s in secrets if s and len(s) >= 6]

    def redact(self, text: str) -> str:
        redacted = text
        for secret in self._secrets:
            if secret in redacted:
                redacted = redacted.replace(secret, "[REDACTED]")
        redacted = _PRIVATE_KEY_RE.sub("[REDACTED_PRIVATE_KEY]", redacted)
        redacted = _TELEGRAM_TOKEN_RE.sub("[REDACTED_BOT_TOKEN]", redacted)
        redacted = _BEARER_RE.sub(r"\1[REDACTED_TOKEN]", redacted)
        return redacted

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self.redact(v) if isinstance(v, str) else v for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self.redact(arg) if isinstance(arg, str) else arg for arg in record.args
                )
        return True


def configure_logging(level: str = "INFO", secrets: Iterable[str] = ()) -> SecretRedactionFilter:
    """Configure root logging with secret redaction and reduced HTTP noise."""
    redaction_filter = SecretRedactionFilter(secrets=secrets)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler.addFilter(redaction_filter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Prevent httpx from logging full Telegram bot URLs containing BOT_TOKEN
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext").setLevel(logging.INFO)
    return redaction_filter
