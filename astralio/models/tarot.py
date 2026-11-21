"""Tarot domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TarotSpreadType(StrEnum):
    """Available Tarot spreads."""

    ONE_CARD = "one_card"
    THREE_CARDS = "three_cards"
    RELATIONSHIP = "relationship"
    PATH_CHOICE = "path_choice"


class TarotCard(BaseModel):
    """Single card definition from the 78-card Rider-Waite deck."""

    card_id: str
    name_ru: str
    arcana: str  # "major" | "minor"
    suit_ru: str | None = None
    upright_keywords: str
    reversed_keywords: str
    upright_meaning: str
    reversed_meaning: str
    advice: str


class DrawnCard(BaseModel):
    """A card drawn into a specific spread position."""

    position_index: int = Field(ge=0)
    position_title: str
    card_id: str
    name_ru: str
    is_reversed: bool
    keywords: str
    meaning: str
    advice: str

    def to_firestore_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any]) -> DrawnCard:
        return cls.model_validate(data)


class TarotReading(BaseModel):
    """Persisted Tarot reading document."""

    reading_id: str
    telegram_id: int = Field(gt=0)
    spread_type: TarotSpreadType
    spread_title: str
    question: str | None = None
    cards: list[DrawnCard]
    summary: str
    interpretation_source: str = "local"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_firestore_dict(self) -> dict[str, Any]:
        return {
            "reading_id": self.reading_id,
            "telegram_id": self.telegram_id,
            "spread_type": self.spread_type.value,
            "spread_title": self.spread_title,
            "question": self.question,
            "cards": [c.to_firestore_dict() for c in self.cards],
            "summary": self.summary,
            "interpretation_source": self.interpretation_source,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any]) -> TarotReading:
        raw_dt = data.get("created_at")
        if isinstance(raw_dt, datetime):
            created_at = raw_dt if raw_dt.tzinfo else raw_dt.replace(tzinfo=UTC)
        elif isinstance(raw_dt, str) and raw_dt:
            parsed = datetime.fromisoformat(raw_dt)
            created_at = parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        else:
            created_at = datetime.now(UTC)

        return cls(
            reading_id=str(data["reading_id"]),
            telegram_id=int(data["telegram_id"]),
            spread_type=TarotSpreadType(data["spread_type"]),
            spread_title=str(data["spread_title"]),
            question=data.get("question"),
            cards=[DrawnCard.from_firestore_dict(c) for c in data.get("cards", [])],
            summary=str(data.get("summary", "")),
            interpretation_source=str(data.get("interpretation_source", "local")),
            created_at=created_at,
        )
