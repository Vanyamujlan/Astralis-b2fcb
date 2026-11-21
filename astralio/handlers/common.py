"""Common handlers: /start, /menu, /cancel, unknown commands, invalid callbacks, and error handler."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from astralio.handlers.deps import ensure_user, escape_html, reply_or_edit
from astralio.keyboards.callbacks import CB, is_valid_callback_data
from astralio.keyboards.menus import main_menu_keyboard
from astralio.repositories.base import RepositoryError

logger = logging.getLogger(__name__)


def build_welcome_text(name: str, *, is_new: bool = False) -> str:
    safe_name = escape_html(name)
    greeting = (
        f"Добро пожаловать в <b>Astralio</b>, {safe_name}."
        if is_new
        else f"<b>Astralio</b> — главное меню ({safe_name})."
    )
    return (
        f"✨ {greeting}\n\n"
        "Минималистичный астрологический и таро-помощник:\n"
        "• точные эфемеридные расчёты натальной карты\n"
        "• синастрическая совместимость\n"
        "• персональные прогнозы по реальным транзитам\n"
        "• расклады Таро с историей\n\n"
        "Выберите раздел ниже:"
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start — auto-register user in Firestore and open main menu."""
    context.user_data.clear()
    tg_user = update.effective_user
    if tg_user is None:
        return ConversationHandler.END
    profile = await ensure_user(update, context)
    await reply_or_edit(
        update,
        build_welcome_text(profile.display_name, is_new=True),
        reply_markup=main_menu_keyboard(),
        prefer_new_message=True,
    )
    return ConversationHandler.END


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /menu and return to main menu callback."""
    context.user_data.clear()
    profile = await ensure_user(update, context)
    await reply_or_edit(
        update,
        build_welcome_text(profile.display_name, is_new=False),
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel any active conversation and return cleanly to the main menu."""
    context.user_data.clear()
    await reply_or_edit(
        update,
        "Операция отменена. Вы вернулись в главное меню Astralio.",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gracefully handle unsupported slash commands."""
    await ensure_user(update, context)
    await reply_or_edit(
        update,
        "Неизвестная команда.\n\n"
        "Доступные команды: /start, /menu, /cancel.\n"
        "Или воспользуйтесь кнопками главного меню ниже:",
        reply_markup=main_menu_keyboard(),
        prefer_new_message=True,
    )


async def fallback_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Guide users who send plain text outside an active conversation step."""
    await ensure_user(update, context)
    await reply_or_edit(
        update,
        "Выберите нужный раздел с помощью кнопок меню ниже или введите /menu.",
        reply_markup=main_menu_keyboard(),
        prefer_new_message=True,
    )


async def invalid_or_stale_callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Catch malformed, spoofed, or stale callback_data safely."""
    query = update.callback_query
    raw_data = query.data if query else None
    if not is_valid_callback_data(raw_data):
        logger.warning(
            "Rejected invalid callback_data=%r from user=%s",
            raw_data,
            update.effective_user.id if update.effective_user else None,
        )
        await reply_or_edit(
            update,
            "Некорректное или устаревшее действие. Откройте актуальное главное меню:",
            reply_markup=main_menu_keyboard(),
        )
        return

    # Valid callback received outside an active wizard state (e.g. old Back/Skip button)
    await reply_or_edit(
        update,
        "Этот шаг уже завершён или устарел. Возвращаю в главное меню Astralio:",
        reply_markup=main_menu_keyboard(),
    )


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catch unhandled Telegram, Firestore, and application errors without leaking secrets."""
    err = context.error
    if isinstance(err, RepositoryError):
        logger.error("Repository error while handling update: %s", err)
        user_msg = (
            "⚠️ Временная ошибка базы данных. Попробуйте повторить действие через несколько секунд."
        )
    elif isinstance(err, TelegramError):
        logger.error("Telegram API error while handling update: %s", type(err).__name__)
        return
    else:
        logger.exception("Unexpected error while handling update", exc_info=err)
        user_msg = (
            "⚠️ Произошла непредвиденная ошибка. Попробуйте ещё раз или вернитесь в главное меню."
        )

    if isinstance(update, Update):
        try:
            await reply_or_edit(
                update,
                user_msg,
                reply_markup=main_menu_keyboard(),
                prefer_new_message=True,
            )
        except Exception:
            logger.debug("Unable to notify user about error.")


def register_common_entry_handlers(app: Application) -> None:
    """Register core commands and global main menu navigation."""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("cancel", cancel_operation))
    app.add_handler(CallbackQueryHandler(menu_command, pattern=f"^{CB.MENU_MAIN}$"))
    app.add_handler(CallbackQueryHandler(cancel_operation, pattern=f"^{CB.NAV_CANCEL}$"))


def register_fallback_handlers(app: Application) -> None:
    """Register low-priority fallbacks for unknown commands, invalid callbacks, and stray text."""
    app.add_handler(CallbackQueryHandler(invalid_or_stale_callback_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text_handler))
    app.add_error_handler(global_error_handler)
