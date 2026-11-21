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
    return {
        "type": "service_account",
        "project_id": settings.firebase_project_id,
        "client_email": settings.firebase_client_email,
        "private_key": settings.normalized_firebase_private_key,
        "token_uri": "https://oauth2.googleapis.com/token",
    }


def create_firestore_client(settings: Settings, app_name: str = "astralio") -> Any:
    """Initialize Firebase Admin app (idempotently) and return a Firestore client.

    Supports an optional named Firestore database via FIREBASE_DATABASE_ID.
    Never logs private keys or credentials.
    """
    try:
        try:
            app = firebase_admin.get_app(app_name)
        except ValueError:
            cred_info = build_service_account_info(settings)
            cred = credentials.Certificate(cred_info)
            app = firebase_admin.initialize_app(
                cred,
                options={"projectId": settings.firebase_project_id},
                name=app_name,
            )

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
        logger.error(
            "Failed to initialize Firebase/Firestore for project=%s: %s",
            settings.firebase_project_id,
            type(exc).__name__,
        )
        raise FirebaseInitError(
            "Не удалось подключиться к Firebase Firestore. Проверьте переменные окружения "
            "FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL и FIREBASE_PRIVATE_KEY."
        ) from exc
