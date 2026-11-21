"""Telegram update handler registration."""

from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler

from astralio.handlers.common import register_common_entry_handlers, register_fallback_handlers
from astralio.handlers.compatibility import (
    build_compatibility_conversation,
    show_compatibility_menu,
)
from astralio.handlers.forecast import register_forecast_handlers
from astralio.handlers.help import build_help_conversation, show_help_guide, show_help_menu
from astralio.handlers.natal import (
    build_natal_conversation,
    calculate_natal_from_profile,
    show_natal_menu,
)
from astralio.handlers.premium import register_premium_handlers
from astralio.handlers.profile import build_profile_conversation, show_profile
from astralio.handlers.tarot import build_tarot_conversation, show_tarot_history, show_tarot_menu
from astralio.keyboards.callbacks import CB


def register_all_handlers(app: Application) -> None:
    """Register all Astralio handlers in strict priority order.

    Order matters in python-telegram-bot (group 0):
    1. ConversationHandlers first, so their states and fallbacks (/start, /menu, /cancel,
       nav:cancel, menu:main) always terminate active conversations cleanly.
    2. Core commands (/start, /menu, /cancel) and section menu CallbackQueryHandlers.
    3. Payment handlers (PreCheckoutQueryHandler, SUCCESSFUL_PAYMENT).
    4. Low-priority fallbacks (invalid callback_data, unknown commands, stray text, error handler).
    """
    # 1. ConversationHandlers (wizards)
    app.add_handler(build_profile_conversation())
    app.add_handler(build_natal_conversation())
    app.add_handler(build_compatibility_conversation())
    app.add_handler(build_tarot_conversation())
    app.add_handler(build_help_conversation())

    # 2. Global commands & top-level section navigation
    register_common_entry_handlers(app)
    app.add_handler(CallbackQueryHandler(show_profile, pattern=f"^{CB.MENU_PROFILE}$"))
    app.add_handler(CallbackQueryHandler(show_natal_menu, pattern=f"^{CB.MENU_NATAL}$"))
    app.add_handler(
        CallbackQueryHandler(calculate_natal_from_profile, pattern=f"^{CB.NATAL_FROM_PROFILE}$")
    )
    app.add_handler(CallbackQueryHandler(show_compatibility_menu, pattern=f"^{CB.MENU_COMPAT}$"))
    register_forecast_handlers(app)
    app.add_handler(CallbackQueryHandler(show_tarot_menu, pattern=f"^{CB.MENU_TAROT}$"))
    app.add_handler(CallbackQueryHandler(show_tarot_history, pattern=f"^{CB.TAROT_HISTORY}$"))
    app.add_handler(CallbackQueryHandler(show_help_menu, pattern=f"^{CB.MENU_HELP}$"))
    app.add_handler(CallbackQueryHandler(show_help_guide, pattern=f"^{CB.HELP_GUIDE}$"))

    # 3. Premium & Telegram Stars payment handlers
    register_premium_handlers(app)

    # 4. Low-priority fallbacks & global error handler
    register_fallback_handlers(app)


__all__ = ["register_all_handlers"]
