"""Firebase Admin SDK & Google Cloud Firestore initialization."""

from __future__ import annotations

import logging
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

from astralio.config import Settings

logger = logging.getLogger(__name__)


class FirebaseInitError(RuntimeError):
    """Raised when Firebase Admin SDK or Firestore cannot be initialized."""


def build_service_account_info(settings: Settings) -> dict[str, str]:
    """Build Firebase Admin certificate dictionary from environment settings."""
    if not settings.has_firebase_admin_credentials:
        raise FirebaseInitError(
            "Отсутствуют обязательные переменные Firebase Admin SDK: "
            "FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY."
        )
    assert settings.firebase_project_id is not None
    assert settings.firebase_client_email is not None
    return {
        "type": "service_account",
        "project_id": settings.firebase_project_id,
        "client_email": settings.firebase_client_email,
        "private_key": settings.normalized_firebase_private_key,
        "token_uri": "https://oauth2.googleapis.com/token",
    }


def _sanitize_error_message(exc: Exception, secrets: list[str]) -> str:
    """Return a short, secret-free summary of an initialization exception."""
    msg = str(exc)
    for secret in secrets:
        if secret and secret in msg:
            msg = msg.replace(secret, "[REDACTED]")
    # Strip any PEM markers or long base64-like runs defensively
    import re

    msg = re.sub(r"-----BEGIN.*?-----END[^-]*-----", "[REDACTED_KEY]", msg, flags=re.DOTALL)
    msg = re.sub(r"[A-Za-z0-9+/=_-]{32,}", "[REDACTED_TOKEN]", msg)
    return " ".join(msg.split())[:200]


def create_firestore_client(settings: Settings, app_name: str = "astralio") -> Any:
    """Initialize Firebase Admin app (idempotently) and return a Firestore client.

    Supports an optional named Firestore database via FIREBASE_DATABASE_ID.
    Never logs private keys or credentials.
    """
    stage = "get_app"
    try:
        try:
            app = firebase_admin.get_app(app_name)
        except ValueError:
            stage = "build_info"
            cred_info = build_service_account_info(settings)
            stage = "certificate"
            cred = credentials.Certificate(cred_info)
            stage = "initialize_app"
            app = firebase_admin.initialize_app(
                cred,
                options={"projectId": settings.firebase_project_id},
                name=app_name,
            )

        stage = "firestore_client"
        if settings.firebase_database_id:
            logger.info(
                "Connecting to Firestore project=%s database_id=%s",
                settings.firebase_project_id,
                settings.firebase_database_id,
            )
            return firestore.client(app=app, database_id=settings.firebase_database_id)

        logger.info(
            "Connecting to Firestore project=%s database_id=(default)", settings.firebase_project_id
        )
        return firestore.client(app=app)
    except Exception as exc:
        norm_key = settings.normalized_firebase_private_key
        key_lines = norm_key.splitlines()
        body_str = "".join(line for line in key_lines if not line.startswith("-----"))
        valid_b64_chars = bool(body_str) and all(ch.isalnum() or ch in "+/=" for ch in body_str)
        has_valid_email = bool(
            settings.firebase_client_email and "@" in settings.firebase_client_email
        )
        safe_reason = _sanitize_error_message(exc, settings.secret_values())
        logger.error(
            "Failed to initialize Firebase/Firestore for project=%s at stage=%s: %s (%s) "
            "[has_begin=%s, has_end=%s, key_lines=%d, body_len=%d, b64_ok=%s, email_ok=%s]",
            settings.firebase_project_id,
            stage,
            type(exc).__name__,
            safe_reason,
            "BEGIN" in norm_key and "PRIVATE KEY" in norm_key,
            "END" in norm_key and "PRIVATE KEY" in norm_key,
            len(key_lines),
            len(body_str),
            valid_b64_chars,
            has_valid_email,
        )
        raise FirebaseInitError(
            "Не удалось подключиться к Firebase Firestore. Проверьте переменные окружения "
            "FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL и FIREBASE_PRIVATE_KEY."
        ) from exc
