"""Premium tariffs and idempotent Telegram Stars payment models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from astralio.models.user import SubscriptionPlan


class PaymentStatus(StrEnum):
    """Lifecycle status of a payment transaction."""

    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class PremiumTariff(BaseModel):
    """Subscription tariff specification ready for Telegram Stars (XTR)."""

    plan: SubscriptionPlan
    title: str
    duration_days: int = Field(gt=0)
    price_stars: int = Field(gt=0)
    currency: str = "XTR"
    description: str
    features: list[str]


class PaymentRecord(BaseModel):
    """Idempotent payment ledger entry keyed by Telegram payment charge ID."""

    charge_id: str = Field(min_length=1)
    telegram_id: int = Field(gt=0)
    plan: SubscriptionPlan
    amount: int = Field(gt=0)
    currency: str = "XTR"
    invoice_payload: str
    status: PaymentStatus = PaymentStatus.CONFIRMED
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_firestore_dict(self) -> dict[str, Any]:
        return {
            "charge_id": self.charge_id,
            "telegram_id": self.telegram_id,
            "plan": self.plan.value,
            "amount": self.amount,
            "currency": self.currency,
            "invoice_payload": self.invoice_payload,
            "status": self.status.value,
            "processed_at": self.processed_at.isoformat(),
        }

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any]) -> PaymentRecord:
        raw_dt = data.get("processed_at")
        if isinstance(raw_dt, datetime):
            processed_at = raw_dt if raw_dt.tzinfo else raw_dt.replace(tzinfo=UTC)
        elif isinstance(raw_dt, str) and raw_dt:
            parsed = datetime.fromisoformat(raw_dt)
            processed_at = parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        else:
            processed_at = datetime.now(UTC)

        return cls(
            charge_id=str(data["charge_id"]),
            telegram_id=int(data["telegram_id"]),
            plan=SubscriptionPlan(data["plan"]),
            amount=int(data["amount"]),
            currency=str(data.get("currency", "XTR")),
            invoice_payload=str(data.get("invoice_payload", "")),
            status=PaymentStatus(data.get("status", PaymentStatus.CONFIRMED.value)),
            processed_at=processed_at,
        )
