"""Premium tariffs, subscription status check, and Telegram Stars payment handlers."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from telegram import LabeledPrice, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from astralio.handlers.deps import ensure_user, get_services, reply_or_edit
from astralio.keyboards.callbacks import CB, parse_callback_data
from astralio.keyboards.menus import premium_menu_keyboard
from astralio.models.user import SubscriptionPlan
from astralio.repositories.base import DuplicatePaymentError

logger = logging.getLogger(__name__)


async def show_premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display tariffs and real subscription status."""
    profile = await ensure_user(update, context)
    services = get_services(context)
    await reply_or_edit(
        update,
        services.premium_service.format_premium_overview(profile),
        reply_markup=premium_menu_keyboard(),
    )


async def check_premium_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Explicitly check and display current subscription status from Firestore."""
    profile = await ensure_user(update, context)
    now = datetime.now(UTC)
    sub = profile.subscription
    if sub.is_currently_active(now) and sub.expires_at is not None:
        text = (
            "✅ <b>Подписка Astralio Premium активна</b>\n\n"
            f"• Тариф: <code>{sub.plan.value}</code>\n"
            f"• Действует до: <b>{sub.expires_at.strftime('%d.%m.%Y %H:%M UTC')}</b>"
        )
    else:
        text = (
            "🔍 <b>Проверка статуса подписки</b>\n\n"
            "Сейчас у вас активен <b>Базовый (бесплатный)</b> тариф.\n"
            "Активация Premium выполняется автоматически только после подтверждённой оплаты "
            "через Telegram Stars."
        )
    await reply_or_edit(update, text, reply_markup=premium_menu_keyboard())


async def select_premium_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle tariff selection: send real Telegram Stars invoice when enabled, never fake payment."""
    profile = await ensure_user(update, context)
    services = get_services(context)
    query = update.callback_query
    parsed = parse_callback_data(query.data if query else None)
    if parsed is None or parsed[2] is None:
        await show_premium_menu(update, context)
        return

    try:
        plan = SubscriptionPlan(parsed[2])
    except ValueError:
        await show_premium_menu(update, context)
        return

    tariff = services.premium_service.get_tariff(plan)
    if tariff is None:
        await show_premium_menu(update, context)
        return

    if not services.premium_service.telegram_stars_enabled:
        await reply_or_edit(
            update,
            f"⭐ <b>{tariff.title} — {tariff.price_stars} Stars</b>\n\n"
            f"{tariff.description}\n\n"
            "🔒 Оплата через Telegram Stars сейчас отключена в конфигурации бота "
            "(<code>TELEGRAM_STARS_ENABLED=false</code>).\n"
            "Мы не имитируем оплату и не активируем подписку без реального подтверждения Telegram. "
            "После включения Telegram Stars администратором здесь автоматически откроется "
            "стандартный счёт Telegram Stars (валюта <code>XTR</code>).",
            reply_markup=premium_menu_keyboard(),
        )
        return

    invoice = services.premium_service.build_invoice_spec(plan, profile.telegram_id)
    if query is not None:
        await query.answer()
    if update.effective_chat is not None:
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=invoice.title,
            description=invoice.description,
            payload=invoice.payload,
            provider_token="",  # Required to be empty string for Telegram Stars (XTR)
            currency=invoice.currency,
            prices=[LabeledPrice(label=invoice.title, amount=invoice.amount_stars)],
        )


async def handle_pre_checkout_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Validate Telegram Stars pre-checkout request before Telegram charges the user."""
    pre_checkout = update.pre_checkout_query
    if pre_checkout is None:
        return
    services = get_services(context)
    ok, error_message = services.premium_service.validate_pre_checkout(
        invoice_payload=pre_checkout.invoice_payload,
        currency=pre_checkout.currency,
        total_amount=pre_checkout.total_amount,
        telegram_id=pre_checkout.from_user.id,
    )
    await pre_checkout.answer(ok=ok, error_message=error_message)


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Activate Premium idempotently ONLY upon real confirmed Telegram Stars payment."""
    message = update.message
    tg_user = update.effective_user
    if message is None or message.successful_payment is None or tg_user is None:
        return

    payment = message.successful_payment
    services = get_services(context)
    try:
        new_sub, _applied = await services.premium_service.confirm_telegram_stars_payment(
            telegram_id=tg_user.id,
            charge_id=payment.telegram_payment_charge_id,
            invoice_payload=payment.invoice_payload,
            currency=payment.currency,
            total_amount=payment.total_amount,
        )
    except DuplicatePaymentError:
        logger.info("Duplicate payment update ignored for user=%s", tg_user.id)
        await reply_or_edit(
            update,
            "ℹ️ Этот платёж уже был обработан ранее — повторное списание не требуется.",
            reply_markup=premium_menu_keyboard(),
            prefer_new_message=True,
        )
        return
    except ValueError as exc:
        logger.warning("Rejected invalid successful_payment for user=%s: %s", tg_user.id, exc)
        await reply_or_edit(
            update,
            f"⚠️ Не удалось подтвердить платёж: {exc}",
            reply_markup=premium_menu_keyboard(),
            prefer_new_message=True,
        )
        return

    expires_str = new_sub.expires_at.strftime("%d.%m.%Y %H:%M UTC") if new_sub.expires_at else "—"
    await reply_or_edit(
        update,
        "✅ <b>Оплата Telegram Stars подтверждена!</b>\n\n"
        f"Astralio Premium активирован до <b>{expires_str}</b>.",
        reply_markup=premium_menu_keyboard(),
        prefer_new_message=True,
    )


def register_premium_handlers(app: Application) -> None:
    buy_pattern = f"^({CB.PREMIUM_BUY_MONTHLY}|{CB.PREMIUM_BUY_QUARTERLY}|{CB.PREMIUM_BUY_YEARLY})$"
    app.add_handler(CallbackQueryHandler(show_premium_menu, pattern=f"^{CB.MENU_PREMIUM}$"))
    app.add_handler(CallbackQueryHandler(check_premium_status, pattern=f"^{CB.PREMIUM_STATUS}$"))
    app.add_handler(CallbackQueryHandler(select_premium_plan, pattern=buy_pattern))
    app.add_handler(PreCheckoutQueryHandler(handle_pre_checkout_query))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handle_successful_payment))
