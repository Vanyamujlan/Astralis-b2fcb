"""Premium tariffs, subscription verification, and idempotent Telegram Stars architecture."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from astralio.models.payment import PaymentRecord, PaymentStatus, PremiumTariff
from astralio.models.user import SubscriptionInfo, SubscriptionPlan, UserProfile
from astralio.repositories.payment_repository import PaymentRepository
from astralio.repositories.user_repository import UserRepository

STARS_CURRENCY = "XTR"
PAYLOAD_PREFIX = "astralio:stars"

PREMIUM_TARIFFS: dict[SubscriptionPlan, PremiumTariff] = {
    SubscriptionPlan.MONTHLY: PremiumTariff(
        plan=SubscriptionPlan.MONTHLY,
        title="Astralio Premium — 1 месяц",
        duration_days=30,
        price_stars=199,
        currency=STARS_CURRENCY,
        description="Полный доступ к расширенным разборам натальной карты, совместимости и Таро на 30 дней.",
        features=[
            "Расширенные разборы натальной карты и аспектов",
            "Неограниченные расчёты совместимости",
            "Расширенная история раскладов Таро",
            "Приоритетные AI-интерпретации (при подключённом AI-модуле)",
        ],
    ),
    SubscriptionPlan.QUARTERLY: PremiumTariff(
        plan=SubscriptionPlan.QUARTERLY,
        title="Astralio Premium — 3 месяца",
        duration_days=90,
        price_stars=499,
        currency=STARS_CURRENCY,
        description="Доступ к Premium-функциям на 90 дней с выгодой ~16%.",
        features=[
            "Все возможности месячного тарифа",
            "Экономия по сравнению с помесячной оплатой",
            "Доступ к недельным транзитным сводкам",
        ],
    ),
    SubscriptionPlan.YEARLY: PremiumTariff(
        plan=SubscriptionPlan.YEARLY,
        title="Astralio Premium — 1 год",
        duration_days=365,
        price_stars=1499,
        currency=STARS_CURRENCY,
        description="Годовой доступ к Astralio Premium с максимальной выгодой.",
        features=[
            "Все возможности Astralio Premium на 365 дней",
            "Максимальная выгода на годовой период",
            "Ранний доступ к новым астрологическим модулям",
        ],
    ),
}


@dataclass(frozen=True, slots=True)
class StarsInvoiceSpec:
    """Validated specification for Telegram Bot API `send_invoice` with Telegram Stars."""

    title: str
    description: str
    payload: str
    currency: str
    amount_stars: int
    plan: SubscriptionPlan


class PremiumService:
    """Manages tariffs, subscription status checks, and confirmed Telegram Stars payments.

    Security invariant: NEVER activates Premium without a confirmed Telegram payment
    charge ID recorded idempotently in PaymentRepository.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        payment_repository: PaymentRepository,
        *,
        telegram_stars_enabled: bool = False,
    ) -> None:
        self._user_repo = user_repository
        self._payment_repo = payment_repository
        self._stars_enabled = telegram_stars_enabled

    @property
    def telegram_stars_enabled(self) -> bool:
        return self._stars_enabled

    def list_tariffs(self) -> list[PremiumTariff]:
        return [
            PREMIUM_TARIFFS[SubscriptionPlan.MONTHLY],
            PREMIUM_TARIFFS[SubscriptionPlan.QUARTERLY],
            PREMIUM_TARIFFS[SubscriptionPlan.YEARLY],
        ]

    def get_tariff(self, plan: SubscriptionPlan) -> PremiumTariff | None:
        return PREMIUM_TARIFFS.get(plan)

    def build_invoice_spec(self, plan: SubscriptionPlan, telegram_id: int) -> StarsInvoiceSpec:
        """Build Telegram Stars invoice payload for a valid paid plan."""
        tariff = PREMIUM_TARIFFS.get(plan)
        if tariff is None:
            raise ValueError(f"Unsupported Premium plan: {plan}")
        payload = f"{PAYLOAD_PREFIX}:{plan.value}:{telegram_id}"
        return StarsInvoiceSpec(
            title=tariff.title,
            description=tariff.description,
            payload=payload,
            currency=STARS_CURRENCY,
            amount_stars=tariff.price_stars,
            plan=plan,
        )

    def validate_pre_checkout(
        self,
        *,
        invoice_payload: str,
        currency: str,
        total_amount: int,
        telegram_id: int,
    ) -> tuple[bool, str | None]:
        """Validate Telegram `pre_checkout_query` before approving charge."""
        if not self._stars_enabled:
            return False, "Оплата через Telegram Stars пока отключена на сервере."
        if currency != STARS_CURRENCY:
            return False, "Неподдерживаемая валюта оплаты."

        parsed = self._parse_payload(invoice_payload)
        if parsed is None:
            return False, "Некорректные данные счёта."
        plan, payload_user_id = parsed
        if payload_user_id != telegram_id:
            return False, "Счёт предназначен для другого пользователя."

        tariff = PREMIUM_TARIFFS.get(plan)
        if tariff is None or total_amount != tariff.price_stars:
            return False, "Сумма платежа не совпадает с выбранным тарифом."
        return True, None

    async def confirm_telegram_stars_payment(
        self,
        *,
        telegram_id: int,
        charge_id: str,
        invoice_payload: str,
        currency: str,
        total_amount: int,
        now: datetime | None = None,
    ) -> tuple[SubscriptionInfo, bool]:
        """Idempotently process a confirmed Telegram Stars `successful_payment`.

        Returns `(subscription_info, newly_applied)`.
        If `charge_id` was already processed, raises DuplicatePaymentError from repository
        or returns `(current_subscription, False)` without double-extending.
        """
        if not charge_id or not charge_id.strip():
            raise ValueError("Отсутствует подтверждённый идентификатор платежа Telegram.")

        valid, error_msg = self.validate_pre_checkout(
            invoice_payload=invoice_payload,
            currency=currency,
            total_amount=total_amount,
            telegram_id=telegram_id,
        )
        if not valid:
            raise ValueError(error_msg or "Платёж не прошёл проверку.")

        parsed = self._parse_payload(invoice_payload)
        assert parsed is not None
        plan, _ = parsed
        tariff = PREMIUM_TARIFFS[plan]
        current_time = now or datetime.now(UTC)

        record = PaymentRecord(
            charge_id=charge_id.strip(),
            telegram_id=telegram_id,
            plan=plan,
            amount=total_amount,
            currency=currency,
            invoice_payload=invoice_payload,
            status=PaymentStatus.CONFIRMED,
            processed_at=current_time,
        )
        # Atomic idempotency check in Firestore payments/{charge_id}
        await self._payment_repo.record_payment_idempotent(record)

        user = await self._user_repo.get_user(telegram_id)
        base_start = current_time
        if user is not None and user.subscription.is_currently_active(current_time):
            assert user.subscription.expires_at is not None
            base_start = user.subscription.expires_at

        new_sub = SubscriptionInfo(
            plan=plan,
            is_active=True,
            activated_at=current_time,
            expires_at=base_start + timedelta(days=tariff.duration_days),
            last_payment_charge_id=charge_id.strip(),
        )
        await self._user_repo.update_subscription(telegram_id, new_sub)
        return new_sub, True

    @staticmethod
    def _parse_payload(payload: str) -> tuple[SubscriptionPlan, int] | None:
        parts = payload.split(":")
        if len(parts) != 4 or f"{parts[0]}:{parts[1]}" != PAYLOAD_PREFIX:
            return None
        try:
            plan = SubscriptionPlan(parts[2])
            user_id = int(parts[3])
        except (ValueError, TypeError):
            return None
        if plan == SubscriptionPlan.FREE or user_id <= 0:
            return None
        return plan, user_id

    def format_premium_overview(self, profile: UserProfile) -> str:
        """Render tariffs page and current real subscription status."""
        now = datetime.now(UTC)
        sub = profile.subscription
        if sub.is_currently_active(now) and sub.expires_at is not None:
            tariff = PREMIUM_TARIFFS.get(sub.plan)
            plan_label = tariff.title if tariff else sub.plan.value
            status_block = (
                f"✅ <b>Статус подписки:</b> Активна ({plan_label})\n"
                f"⏳ Действует до: {sub.expires_at.strftime('%d.%m.%Y %H:%M UTC')}"
            )
        elif sub.expires_at is not None and sub.plan != SubscriptionPlan.FREE:
            status_block = (
                f"⌛ <b>Статус подписки:</b> Срок действия истёк "
                f"({sub.expires_at.strftime('%d.%m.%Y')})\n"
                "Текущий тариф: Базовый (бесплатный)"
            )
        else:
            status_block = "🔹 <b>Статус подписки:</b> Базовый (бесплатный)"

        lines = [
            "⭐ <b>Astralio Premium</b>",
            "",
            status_block,
            "",
            "<b>Доступные тарифы (Telegram Stars):</b>",
        ]
        for tariff in self.list_tariffs():
            lines.append(
                f"• <b>{tariff.title}</b> — {tariff.price_stars} ⭐ ({tariff.duration_days} дн.)"
            )

        lines.extend(
            [
                "",
                "<b>Что открывает Premium:</b>",
                "• Расширенные интерпретации натальной карты и транзитов",
                "• Неограниченные разборы совместимости",
                "• Полная история раскладов Таро",
            ]
        )

        if not self._stars_enabled:
            lines.extend(
                [
                    "",
                    "ℹ️ Оплата через Telegram Stars подготовлена на уровне архитектуры, "
                    "но сейчас отключена в настройках сервера (<code>TELEGRAM_STARS_ENABLED=false</code>). "
                    "Подписка активируется только после реального подтверждённого платежа Telegram.",
                ]
            )
        return "\n".join(lines)
