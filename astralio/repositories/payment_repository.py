"""Idempotent Firestore payment ledger repository."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from astralio.models.payment import PaymentRecord
from astralio.repositories.base import DuplicatePaymentError, RepositoryError

logger = logging.getLogger(__name__)


class PaymentRepository:
    """Stores confirmed payments keyed by charge_id to prevent duplicate processing."""

    COLLECTION = "payments"

    def __init__(self, db: Any) -> None:
        self._db = db

    def _doc_ref(self, charge_id: str) -> Any:
        return self._db.collection(self.COLLECTION).document(charge_id)

    async def get_payment(self, charge_id: str) -> PaymentRecord | None:
        """Look up an existing payment record by Telegram payment charge ID."""
        try:
            snapshot = await asyncio.to_thread(self._doc_ref(charge_id).get)
            if not snapshot.exists:
                return None
            return PaymentRecord.from_firestore_dict(snapshot.to_dict() or {})
        except Exception as exc:
            logger.error("Firestore get_payment failed: %s", type(exc).__name__)
            raise RepositoryError("Не удалось проверить статус платежа.") from exc

    async def record_payment_idempotent(self, record: PaymentRecord) -> bool:
        """Atomically create a payment document if it does not already exist.

        Returns True if recorded for the first time, or raises DuplicatePaymentError
        if this charge_id was already processed.
        """
        doc_ref = self._doc_ref(record.charge_id)
        try:
            if hasattr(doc_ref, "create"):
                try:
                    await asyncio.to_thread(doc_ref.create, record.to_firestore_dict())
                    return True
                except Exception as exc:
                    if exc.__class__.__name__ in {"AlreadyExists", "Conflict"}:
                        raise DuplicatePaymentError(
                            f"Платёж {record.charge_id} уже был обработан ранее."
                        ) from exc
                    raise
            # Fallback for simplified mock clients without .create()
            snapshot = await asyncio.to_thread(doc_ref.get)
            if snapshot.exists:
                raise DuplicatePaymentError(f"Платёж {record.charge_id} уже был обработан ранее.")
            await asyncio.to_thread(doc_ref.set, record.to_firestore_dict())
            return True
        except DuplicatePaymentError:
            raise
        except Exception as exc:
            logger.error("Firestore record_payment_idempotent failed: %s", type(exc).__name__)
            raise RepositoryError("Не удалось зафиксировать платёж в базе данных.") from exc
