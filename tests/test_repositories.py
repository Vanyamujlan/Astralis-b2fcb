"""Tests for Firestore repositories using in-memory and error-injecting mocks."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from unittest.mock import MagicMock

import pytest

from astralio.models.feedback import FeedbackMessage
from astralio.models.payment import PaymentRecord
from astralio.models.user import BirthData, SubscriptionPlan
from astralio.repositories.base import DuplicatePaymentError, RepositoryError
from astralio.repositories.feedback_repository import FeedbackRepository
from astralio.repositories.payment_repository import PaymentRepository
from astralio.repositories.user_repository import UserRepository
from tests.conftest import FakeFirestoreClient


@pytest.mark.asyncio
async def test_user_repository_registration_and_safe_merge() -> None:
    db = FakeFirestoreClient()
    repo = UserRepository(db)

    profile, created = await repo.get_or_create_user(
        telegram_id=42,
        first_name="Иван",
        username="ivan_old",
    )
    assert created is True
    assert profile.telegram_id == 42
    assert profile.username == "ivan_old"

    await repo.update_birth_data(
        42,
        BirthData(
            birth_date=date(1995, 5, 15),
            birth_time=time(14, 30),
            birth_place="Москва, Россия",
            latitude=55.7558,
            longitude=37.6173,
            timezone="Europe/Moscow",
        ),
    )

    # Syncing changed username must preserve saved birth_data safely
    profile2, created2 = await repo.get_or_create_user(
        telegram_id=42,
        first_name="Иван",
        username="ivan_new",
    )
    assert created2 is False
    assert profile2.username == "ivan_new"
    assert profile2.birth_data.birth_date == date(1995, 5, 15)
    assert profile2.birth_data.birth_place == "Москва, Россия"


@pytest.mark.asyncio
async def test_payment_repository_deduplicates_charge_ids() -> None:
    db = FakeFirestoreClient()
    repo = PaymentRepository(db)

    record = PaymentRecord(
        charge_id="charge_abc",
        telegram_id=42,
        plan=SubscriptionPlan.MONTHLY,
        amount=199,
        currency="XTR",
        invoice_payload="astralio:stars:monthly:42",
    )
    assert await repo.record_payment_idempotent(record) is True
    loaded = await repo.get_payment("charge_abc")
    assert loaded is not None
    assert loaded.amount == 199

    with pytest.raises(DuplicatePaymentError):
        await repo.record_payment_idempotent(record)


@pytest.mark.asyncio
async def test_feedback_repository_persists_entry() -> None:
    db = FakeFirestoreClient()
    repo = FeedbackRepository(db)

    fb = FeedbackMessage(
        feedback_id="fb_01",
        telegram_id=42,
        username="ivan",
        message="Очень удобная натальная карта!",
        created_at=datetime.now(UTC),
    )
    saved = await repo.save_feedback(fb)
    assert saved.feedback_id == "fb_01"
    assert "feedback/fb_01" in db.store


@pytest.mark.asyncio
async def test_user_repository_wraps_firestore_errors() -> None:
    broken_db = MagicMock()
    broken_db.collection.side_effect = RuntimeError("Firestore unavailable")
    repo = UserRepository(broken_db)

    with pytest.raises(RepositoryError):
        await repo.get_user(42)


@pytest.mark.asyncio
async def test_local_file_store_persists_users_and_deduplicates_payments(tmp_path: object) -> None:
    from pathlib import Path

    from astralio.infrastructure.local_store import LocalFileFirestoreClient

    db_file = Path(str(tmp_path)) / "local_db.json"
    store1 = LocalFileFirestoreClient(db_file)
    user_repo1 = UserRepository(store1)
    pay_repo1 = PaymentRepository(store1)

    await user_repo1.get_or_create_user(telegram_id=99, first_name="Олег", username="oleg")
    record = PaymentRecord(
        charge_id="local_charge_1",
        telegram_id=99,
        plan=SubscriptionPlan.MONTHLY,
        amount=199,
        currency="XTR",
        invoice_payload="astralio:stars:monthly:99",
    )
    assert await pay_repo1.record_payment_idempotent(record) is True

    # Reload from disk into a fresh instance to verify persistence
    store2 = LocalFileFirestoreClient(db_file)
    user_repo2 = UserRepository(store2)
    pay_repo2 = PaymentRepository(store2)

    loaded = await user_repo2.get_user(99)
    assert loaded is not None
    assert loaded.first_name == "Олег"

    with pytest.raises(DuplicatePaymentError):
        await pay_repo2.record_payment_idempotent(record)
