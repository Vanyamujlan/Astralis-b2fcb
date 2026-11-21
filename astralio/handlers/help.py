"""Help guide and feedback submission handlers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from astralio.handlers.common import cancel_operation, menu_command, start_command
from astralio.handlers.deps import ensure_user, get_services, reply_or_edit
from astralio.keyboards.callbacks import CB
from astralio.keyboards.menus import help_menu_keyboard, wizard_nav_keyboard
from astralio.models.feedback import FeedbackMessage
from astralio.services.validators import InputValidationError, validate_feedback_text

HELP_WAIT_FEEDBACK = 0


async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display Help section menu."""
    await ensure_user(update, context)
    await reply_or_edit(
        update,
        "❓ <b>Помощь Astralio</b>\n\n"
        "Здесь вы найдёте инструкцию по всем функциям бота и форму обратной связи.\n"
        "Основные команды: /start, /menu, /cancel.",
        reply_markup=help_menu_keyboard(),
    )
    return ConversationHandler.END


async def show_help_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display clear feature instructions."""
    await ensure_user(update, context)
    await reply_or_edit(
        update,
        "📖 <b>Инструкция по функциям Astralio</b>\n\n"
        "• <b>Натальная карта</b> — пошаговый ввод даты, времени и места рождения. "
        "Положения Солнца, Луны, планет, Асцендента и домов рассчитываются через Swiss Ephemeris. "
        "Если время неизвестно, бот честно указывает ограничения расчёта.\n"
        "• <b>Совместимость</b> — сравнение карт двух людей (синастрия) с понятными выводами.\n"
        "• <b>Прогнозы</b> — ежедневный и недельный расчёт реальных транзитов к вашей натальной карте.\n"
        "• <b>Таро</b> — 4 расклада из полной колоды (78 карт, без повторов, прямое/перевёрнутое положение) "
        "с автоматическим сохранением истории.\n"
        "• <b>Профиль</b> — просмотр и изменение сохранённых данных рождения.\n"
        "• <b>Premium</b> — тарифы и проверка статуса подписки.\n\n"
        "На любом шаге ввода работают кнопки «Назад», «Отмена» и команда /cancel.",
        reply_markup=help_menu_keyboard(),
    )


async def start_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start step-by-step feedback entry."""
    await ensure_user(update, context)
    await reply_or_edit(
        update,
        "✉️ <b>Обратная связь</b>\n\n"
        "Напишите ваше сообщение, идею или описание проблемы (от 5 до 2000 символов):",
        reply_markup=wizard_nav_keyboard(include_back=True),
    )
    return HELP_WAIT_FEEDBACK


async def receive_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return HELP_WAIT_FEEDBACK
    try:
        clean_text = validate_feedback_text(update.message.text)
    except InputValidationError as exc:
        await reply_or_edit(
            update,
            f"⚠️ {exc}\n\nПопробуйте отправить сообщение снова:",
            reply_markup=wizard_nav_keyboard(include_back=True),
            prefer_new_message=True,
        )
        return HELP_WAIT_FEEDBACK

    profile = await ensure_user(update, context)
    services = get_services(context)
    entry = FeedbackMessage(
        feedback_id=uuid.uuid4().hex[:16],
        telegram_id=profile.telegram_id,
        username=profile.username,
        message=clean_text,
        created_at=datetime.now(UTC),
    )
    await services.feedback_repository.save_feedback(entry)
    await reply_or_edit(
        update,
        "✅ <b>Спасибо за обратную связь!</b>\n\nВаше сообщение сохранено и передано команде Astralio.",
        reply_markup=help_menu_keyboard(),
        prefer_new_message=True,
    )
    return ConversationHandler.END


def build_help_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_feedback, pattern=f"^{CB.HELP_FEEDBACK}$"),
        ],
        states={
            HELP_WAIT_FEEDBACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_feedback),
                CallbackQueryHandler(show_help_menu, pattern=f"^{CB.NAV_BACK}$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_operation, pattern=f"^{CB.NAV_CANCEL}$"),
            CallbackQueryHandler(menu_command, pattern=f"^{CB.MENU_MAIN}$"),
            CommandHandler("start", start_command),
            CommandHandler("cancel", cancel_operation),
            CommandHandler("menu", menu_command),
        ],
        allow_reentry=True,
        per_message=False,
        name="help_feedback_conversation",
    )


def register_help_handlers(app: Application) -> None:
    app.add_handler(build_help_conversation())
    app.add_handler(CallbackQueryHandler(show_help_menu, pattern=f"^{CB.MENU_HELP}$"))
    app.add_handler(CallbackQueryHandler(show_help_guide, pattern=f"^{CB.HELP_GUIDE}$"))
