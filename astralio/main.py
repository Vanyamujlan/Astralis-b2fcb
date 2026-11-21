"""Entry point for running Astralio Telegram Bot via polling (Railway Worker compatible)."""

from __future__ import annotations

import logging
import sys

from pydantic import ValidationError

from astralio.app import ALLOWED_UPDATES, build_application
from astralio.config import get_settings
from astralio.infrastructure.firebase import FirebaseInitError
from astralio.infrastructure.logging import configure_logging

logger = logging.getLogger(__name__)


def main() -> int:
    """Load settings, configure safe logging, build Application, and start polling."""
    try:
        settings = get_settings()
    except ValidationError as exc:
        logging.basicConfig(level=logging.ERROR)
        logging.error(
            "Invalid or missing environment configuration (%d validation errors). "
            "Check .env against .env.example.",
            len(exc.errors()),
        )
        return 1

    configure_logging(level=settings.log_level, secrets=settings.secret_values())
    logger.info(
        "Starting Astralio bot | project=%s | ai_enabled=%s | stars_enabled=%s",
        settings.firebase_project_id,
        settings.has_ai_configured,
        settings.telegram_stars_enabled,
    )

    try:
        application = build_application(settings)
    except FirebaseInitError as exc:
        logger.error("Startup aborted: %s", exc)
        return 1

    try:
        application.run_polling(
            allowed_updates=ALLOWED_UPDATES,
            drop_pending_updates=False,
            close_loop=False,
        )
    except KeyboardInterrupt:
        logger.info("Received interrupt signal; Astralio bot stopped gracefully.")
    except Exception as exc:
        logger.exception("Fatal runtime error in Astralio bot: %s", type(exc).__name__)
        return 1

    logger.info("Astralio bot shut down cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
