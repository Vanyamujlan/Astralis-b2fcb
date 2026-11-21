"""Tests for Premium tariffs, subscription status, and idempotent Telegram Stars payments."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from astralio.models.user import SubscriptionInfo, SubscriptionPlan, UserProfile
from astralio.repositories.base import DuplicatePaymentError
from astralio.repositories.payment_repository import PaymentRepository
from astralio.repositories.user_repository import UserRepository
from astralio.services.premium_service import PremiumService
from tests.conftest import FakeFirestoreClient


def test_tariffs_and_status_overview() -> None:
    db = FakeFirestoreClient()
    service = PremiumService(
        UserRepository(db),
        PaymentRepository(db),
        telegram_stars_enabled=False,
    )
    tariffs = service.list_tariffs()
    assert len(tariffs) == 3
    assert all(t.currency == "XTR" for t in tariffs)

    free_user = UserProfile(telegram_id=10, first_name="Мария")
    text_free = service.format_premium_overview(free_user)
    assert "Базовый (бесплатный)" in text_free
    assert "TELEGRAM_STARS_ENABLED=false" in text_free

    active_user = UserProfile(
        telegram_id=11,
        first_name="Олег",
        subscription=SubscriptionInfo(
            plan=SubscriptionPlan.MONTHLY,
            is_active=True,
            activated_at=datetime.now(UTC) - timedelta(days=1),
            expires_at=datetime.now(UTC) + timedelta(days=29),
        ),
    )
    text_active = service.format_premium_overview(active_user)
    assert "Активна" in text_active


def test_pre_checkout_validation_checks_flag_currency_user_and_amount() -> None:
    db = FakeFirestoreClient()
    disabled = PremiumService(
        UserRepository(db), PaymentRepository(db), telegram_stars_enabled=False
    )
    ok, err = disabled.validate_pre_checkout(
        invoice_payload="astralio:stars:monthly:1001",
        currency="XTR",
        total_amount=199,
        telegram_id=1001,
    )
    assert ok is False
    assert err is not None

    enabled = PremiumService(UserRepository(db), PaymentRepository(db), telegram_stars_enabled=True)
    ok_valid, err_valid = enabled.validate_pre_checkout(
        invoice_payload="astralio:stars:monthly:1001",
        currency="XTR",
        total_amount=199,
        telegram_id=1001,
    )
    assert ok_valid is True
    assert err_valid is None

    # Wrong amount
    assert (
        enabled.validate_pre_checkout(
            invoice_payload="astralio:stars:monthly:1001",
            currency="XTR",
            total_amount=1,
            telegram_id=1001,
        )[0]
        is False
    )
    # Wrong currency
    assert (
        enabled.validate_pre_checkout(
            invoice_payload="astralio:stars:monthly:1001",
            currency="USD",
            total_amount=199,
            telegram_id=1001,
        )[0]
        is False
    )
    # Wrong user
    assert (
        enabled.validate_pre_checkout(
            invoice_payload="astralio:stars:monthly:1001",
            currency="XTR",
            total_amount=199,
            telegram_id=9999,
        )[0]
        is False
    )


@pytest.mark.asyncio
async def test_confirmed_stars_payment_is_idempotent() -> None:
    db = FakeFirestoreClient()
    user_repo = UserRepository(db)
    payment_repo = PaymentRepository(db)
    service = PremiumService(user_repo, payment_repo, telegram_stars_enabled=True)

    await user_repo.get_or_create_user(telegram_id=1001, first_name="Анна")
    spec = service.build_invoice_spec(SubscriptionPlan.MONTHLY, 1001)
    now = datetime(2026, 11, 21, 12, 0, tzinfo=UTC)

    sub, applied = await service.confirm_telegram_stars_payment(
        telegram_id=1001,
        charge_id="tg_charge_001",
        invoice_payload=spec.payload,
        currency="XTR",
        total_amount=spec.amount_stars,
        now=now,
    )
    assert applied is True
    assert sub.is_active is True
    assert sub.plan == SubscriptionPlan.MONTHLY
    assert sub.expires_at == now + timedelta(days=30)

    # Replaying the exact same charge_id must be rejected and must NOT double-extend
    with pytest.raises(DuplicatePaymentError):
        await service.confirm_telegram_stars_payment(
            telegram_id=1001,
            charge_id="tg_charge_001",
            invoice_payload=spec.payload,
            currency="XTR",
            total_amount=spec.amount_stars,
            now=now,
        )

    persisted = await user_repo.get_user(1001)
    assert persisted is not None
    assert persisted.subscription.expires_at == now + timedelta(days=30)
