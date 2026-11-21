"""Firestore repository for user feedback messages."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from astralio.models.feedback import FeedbackMessage
from astralio.repositories.base import RepositoryError

logger = logging.getLogger(__name__)


class FeedbackRepository:
    """Persists user feedback entries into the Firestore `feedback` collection."""

    COLLECTION = "feedback"

    def __init__(self, db: Any) -> None:
        self._db = db

    async def save_feedback(self, feedback: FeedbackMessage) -> FeedbackMessage:
        """Save a feedback message to Firestore."""
        try:
            doc_ref = self._db.collection(self.COLLECTION).document(feedback.feedback_id)
            await asyncio.to_thread(doc_ref.set, feedback.to_firestore_dict())
            return feedback
        except Exception as exc:
            logger.error(
                "Firestore save_feedback failed for user=%s: %s",
                feedback.telegram_id,
                type(exc).__name__,
            )
            raise RepositoryError("Не удалось сохранить обратную связь.") from exc
