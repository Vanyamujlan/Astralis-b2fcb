"""Feedback message model."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class FeedbackMessage(BaseModel):
    """User feedback entry stored in Firestore."""

    feedback_id: str
    telegram_id: int = Field(gt=0)
    username: str | None = None
    message: str = Field(min_length=3, max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_firestore_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
        }
