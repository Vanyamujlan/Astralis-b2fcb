"""User profile, birth data, and subscription models."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SubscriptionPlan(StrEnum):
    """Supported Astralio subscription tiers."""

    FREE = "free"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BirthData(BaseModel):
    """Birth details used for natal chart, compatibility, and transit calculations."""

    birth_date: date | None = None
    birth_time: time | None = None
    birth_time_unknown: bool = False
    birth_place: str | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    timezone: str | None = None

    @property
    def has_birth_date(self) -> bool:
        return self.birth_date is not None

    @property
    def has_exact_time(self) -> bool:
        return self.birth_time is not None and not self.birth_time_unknown

    @property
    def has_coordinates(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    @property
    def is_complete_for_natal(self) -> bool:
        return self.birth_date is not None and (
            self.birth_time is not None or self.birth_time_unknown
        )

    def to_firestore_dict(self) -> dict[str, Any]:
        return {
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "birth_time": self.birth_time.strftime("%H:%M") if self.birth_time else None,
            "birth_time_unknown": self.birth_time_unknown,
            "birth_place": self.birth_place,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
        }

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any] | None) -> BirthData:
        if not data:
            return cls()
        raw_date = data.get("birth_date")
        raw_time = data.get("birth_time")
        parsed_date = (
            date.fromisoformat(raw_date) if isinstance(raw_date, str) and raw_date else None
        )
        parsed_time = (
            time.fromisoformat(raw_time) if isinstance(raw_time, str) and raw_time else None
        )
        return cls(
            birth_date=parsed_date,
            birth_time=parsed_time,
            birth_time_unknown=bool(data.get("birth_time_unknown", False)),
            birth_place=data.get("birth_place"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            timezone=data.get("timezone"),
        )


class SubscriptionInfo(BaseModel):
    """User subscription state persisted in Firestore."""

    plan: SubscriptionPlan = SubscriptionPlan.FREE
    is_active: bool = False
    activated_at: datetime | None = None
    expires_at: datetime | None = None
    last_payment_charge_id: str | None = None

    def is_currently_active(self, now: datetime | None = None) -> bool:
        """Check whether subscription is valid at the given UTC moment."""
        if not self.is_active or self.plan == SubscriptionPlan.FREE:
            return False
        if self.expires_at is None:
            return False
        current = now or datetime.now(UTC)
        expires = (
            self.expires_at
            if self.expires_at.tzinfo is not None
            else self.expires_at.replace(tzinfo=UTC)
        )
        return expires > current

    def to_firestore_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.value,
            "is_active": self.is_active,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_payment_charge_id": self.last_payment_charge_id,
        }

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any] | None) -> SubscriptionInfo:
        if not data:
            return cls()
        raw_plan = data.get("plan", SubscriptionPlan.FREE.value)
        try:
            plan = SubscriptionPlan(raw_plan)
        except ValueError:
            plan = SubscriptionPlan.FREE

        def _parse_dt(val: Any) -> datetime | None:
            if isinstance(val, datetime):
                return val if val.tzinfo else val.replace(tzinfo=UTC)
            if isinstance(val, str) and val:
                parsed = datetime.fromisoformat(val)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
            return None

        return cls(
            plan=plan,
            is_active=bool(data.get("is_active", False)),
            activated_at=_parse_dt(data.get("activated_at")),
            expires_at=_parse_dt(data.get("expires_at")),
            last_payment_charge_id=data.get("last_payment_charge_id"),
        )


class UserProfile(BaseModel):
    """Registered Telegram user document stored in Firestore `users/{telegram_id}`."""

    telegram_id: int = Field(gt=0)
    first_name: str = Field(default="Пользователь")
    last_name: str | None = None
    username: str | None = None
    birth_data: BirthData = Field(default_factory=BirthData)
    subscription: SubscriptionInfo = Field(default_factory=SubscriptionInfo)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def display_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.first_name

    def to_firestore_dict(self) -> dict[str, Any]:
        return {
            "telegram_id": self.telegram_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "birth_data": self.birth_data.to_firestore_dict(),
            "subscription": self.subscription.to_firestore_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any]) -> UserProfile:
        def _parse_dt(val: Any) -> datetime:
            if isinstance(val, datetime):
                return val if val.tzinfo else val.replace(tzinfo=UTC)
            if isinstance(val, str) and val:
                parsed = datetime.fromisoformat(val)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
            return datetime.now(UTC)

        return cls(
            telegram_id=int(data["telegram_id"]),
            first_name=str(data.get("first_name") or "Пользователь"),
            last_name=data.get("last_name"),
            username=data.get("username"),
            birth_data=BirthData.from_firestore_dict(data.get("birth_data")),
            subscription=SubscriptionInfo.from_firestore_dict(data.get("subscription")),
            created_at=_parse_dt(data.get("created_at")),
            updated_at=_parse_dt(data.get("updated_at")),
        )
