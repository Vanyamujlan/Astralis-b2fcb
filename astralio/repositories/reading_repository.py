"""Firestore repository for Tarot reading history."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from astralio.models.tarot import TarotReading
from astralio.repositories.base import RepositoryError

logger = logging.getLogger(__name__)


class ReadingRepository:
    """Stores and queries user Tarot reading history in Firestore subcollections."""

    USERS_COLLECTION = "users"
    TAROT_SUBCOLLECTION = "tarot_readings"

    def __init__(self, db: Any) -> None:
        self._db = db

    def _tarot_collection(self, telegram_id: int) -> Any:
        return (
            self._db.collection(self.USERS_COLLECTION)
            .document(str(telegram_id))
            .collection(self.TAROT_SUBCOLLECTION)
        )

    async def save_tarot_reading(self, reading: TarotReading) -> TarotReading:
        """Persist a completed Tarot reading."""
        try:
            doc_ref = self._tarot_collection(reading.telegram_id).document(reading.reading_id)
            await asyncio.to_thread(doc_ref.set, reading.to_firestore_dict())
            return reading
        except Exception as exc:
            logger.error(
                "Firestore save_tarot_reading failed for user=%s: %s",
                reading.telegram_id,
                type(exc).__name__,
            )
            raise RepositoryError("Не удалось сохранить расклад Таро.") from exc

    async def list_tarot_readings(
        self,
        telegram_id: int,
        *,
        limit: int = 10,
    ) -> list[TarotReading]:
        """Return the user's most recent Tarot readings ordered newest-first."""
        try:
            collection = self._tarot_collection(telegram_id)

            def _query() -> list[dict[str, Any]]:
                query = collection.order_by("created_at", direction="DESCENDING").limit(limit)
                return [doc.to_dict() for doc in query.stream() if doc.to_dict()]

            raw_docs = await asyncio.to_thread(_query)
            return [TarotReading.from_firestore_dict(item) for item in raw_docs]
        except Exception as exc:
            logger.error(
                "Firestore list_tarot_readings failed for user=%s: %s",
                telegram_id,
                type(exc).__name__,
            )
            raise RepositoryError("Не удалось загрузить историю раскладов Таро.") from exc
