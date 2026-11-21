"""Firestore repository for user profiles, birth data, and subscriptions."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from astralio.models.user import BirthData, SubscriptionInfo, UserProfile
from astralio.repositories.base import RepositoryError

logger = logging.getLogger(__name__)


class UserRepository:
    """Async wrapper over Google Cloud Firestore `users` collection."""

    COLLECTION = "users"

    def __init__(self, db: Any) -> None:
        self._db = db

    def _doc_ref(self, telegram_id: int) -> Any:
        return self._db.collection(self.COLLECTION).document(str(telegram_id))

    async def get_user(self, telegram_id: int) -> UserProfile | None:
        """Fetch a user document by Telegram ID."""
        try:
            snapshot = await asyncio.to_thread(self._doc_ref(telegram_id).get)
            if not snapshot.exists:
                return None
            data = snapshot.to_dict() or {}
            data.setdefault("telegram_id", telegram_id)
            return UserProfile.from_firestore_dict(data)
        except Exception as exc:
            logger.error(
                "Firestore get_user failed for user=%s: %s", telegram_id, type(exc).__name__
            )
            raise RepositoryError("Не удалось загрузить профиль из базы данных.") from exc

    async def get_or_create_user(
        self,
        *,
        telegram_id: int,
        first_name: str,
        last_name: str | None = None,
        username: str | None = None,
    ) -> tuple[UserProfile, bool]:
        """Safely register a new user or sync Telegram identity fields for an existing user.

        Returns `(profile, created)`.
        """
        now = datetime.now(UTC)
        clean_first = (first_name or "Пользователь").strip() or "Пользователь"
        try:
            doc_ref = self._doc_ref(telegram_id)
            snapshot = await asyncio.to_thread(doc_ref.get)
            if not snapshot.exists:
                profile = UserProfile(
                    telegram_id=telegram_id,
                    first_name=clean_first,
                    last_name=last_name,
                    username=username,
                    created_at=now,
                    updated_at=now,
                )
                await asyncio.to_thread(doc_ref.set, profile.to_firestore_dict(), True)
                return profile, True

            existing = UserProfile.from_firestore_dict(
                snapshot.to_dict() or {"telegram_id": telegram_id}
            )
            identity_changed = (
                existing.first_name != clean_first
                or existing.last_name != last_name
                or existing.username != username
            )
            if identity_changed:
                existing.first_name = clean_first
                existing.last_name = last_name
                existing.username = username
                existing.updated_at = now
                await asyncio.to_thread(
                    doc_ref.set,
                    {
                        "first_name": clean_first,
                        "last_name": last_name,
                        "username": username,
                        "updated_at": now.isoformat(),
                    },
                    True,
                )
            return existing, False
        except Exception as exc:
            logger.error(
                "Firestore get_or_create_user failed for user=%s: %s",
                telegram_id,
                type(exc).__name__,
            )
            raise RepositoryError("Не удалось зарегистрировать или обновить профиль.") from exc

    async def update_birth_data(self, telegram_id: int, birth_data: BirthData) -> UserProfile:
        """Persist updated birth data safely with merge semantics."""
        now = datetime.now(UTC)
        try:
            doc_ref = self._doc_ref(telegram_id)
            payload = {
                "telegram_id": telegram_id,
                "birth_data": birth_data.to_firestore_dict(),
                "updated_at": now.isoformat(),
            }
            await asyncio.to_thread(doc_ref.set, payload, True)
            updated = await self.get_user(telegram_id)
            if updated is None:
                return UserProfile(
                    telegram_id=telegram_id,
                    birth_data=birth_data,
                    created_at=now,
                    updated_at=now,
                )
            return updated
        except RepositoryError:
            raise
        except Exception as exc:
            logger.error(
                "Firestore update_birth_data failed for user=%s: %s",
                telegram_id,
                type(exc).__name__,
            )
            raise RepositoryError("Не удалось сохранить данные рождения.") from exc

    async def update_subscription(
        self,
        telegram_id: int,
        subscription: SubscriptionInfo,
    ) -> UserProfile:
        """Persist updated subscription status safely."""
        now = datetime.now(UTC)
        try:
            doc_ref = self._doc_ref(telegram_id)
            payload = {
                "telegram_id": telegram_id,
                "subscription": subscription.to_firestore_dict(),
                "updated_at": now.isoformat(),
            }
            await asyncio.to_thread(doc_ref.set, payload, True)
            updated = await self.get_user(telegram_id)
            if updated is None:
                return UserProfile(
                    telegram_id=telegram_id,
                    subscription=subscription,
                    created_at=now,
                    updated_at=now,
                )
            return updated
        except RepositoryError:
            raise
        except Exception as exc:
            logger.error(
                "Firestore update_subscription failed for user=%s: %s",
                telegram_id,
                type(exc).__name__,
            )
            raise RepositoryError("Не удалось обновить статус подписки.") from exc
