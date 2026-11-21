"""Shared handler dependencies and safe Telegram UI helpers."""

from __future__ import annotations

import contextlib
import html
import logging
from dataclasses import dataclass

from telegram import InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from astralio.config import Settings
from astralio.models.user import UserProfile
from astralio.repositories.feedback_repository import FeedbackRepository
from astralio.services.ai_service import AIService
from astralio.services.astrology_service import AstrologyService
from astralio.services.compatibility_service import CompatibilityService
from astralio.services.forecast_service import ForecastService
from astralio.services.premium_service import PremiumService
from astralio.services.tarot_service import TarotService
from astralio.services.user_service import UserService

logger = logging.getLogger(__name__)

SERVICES_BOT_DATA_KEY = "astralio_services"


@dataclass(slots=True)
class ServiceContainer:
    """Container of all wired application services stored in `application.bot_data`."""

    settings: Settings
    user_service: UserService
    astrology_service: AstrologyService
    compatibility_service: CompatibilityService
    forecast_service: ForecastService
    tarot_service: TarotService
    premium_service: PremiumService
    ai_service: AIService
    feedback_repository: FeedbackRepository


def get_services(context: ContextTypes.DEFAULT_TYPE) -> ServiceContainer:
    """Retrieve the typed ServiceContainer from PTB application bot_data."""
    services = context.application.bot_data.get(SERVICES_BOT_DATA_KEY)
    if not isinstance(services, ServiceContainer):
        raise RuntimeError("ServiceContainer is not initialized in application.bot_data.")
    return services


def escape_html(value: str | None) -> str:
    """Escape untrusted user input for Telegram HTML parse mode."""
    return html.escape(value or "", quote=False)


async def ensure_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> UserProfile:
    """Ensure the interacting Telegram user is registered in Firestore."""
    tg_user = update.effective_user
    if tg_user is None:
        raise RuntimeError("Update does not contain effective_user.")
    services = get_services(context)
    profile, _created = await services.user_service.ensure_registered(
        telegram_id=tg_user.id,
        first_name=tg_user.first_name or "Пользователь",
        last_name=tg_user.last_name,
        username=tg_user.username,
    )
    return profile


async def reply_or_edit(
    update: Update,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
    prefer_new_message: bool = False,
) -> None:
    """Safely edit a callback message or send a new message with Telegram HTML formatting."""
    query = update.callback_query
    if query is not None:
        with contextlib.suppress(BadRequest):
            await query.answer()
        if not prefer_new_message and query.message is not None:
            try:
                await query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML,
                )
                return
            except BadRequest as exc:
                if "message is not modified" in str(exc).lower():
                    return
                logger.debug("Fallback to reply_text after edit_message_text error: %s", exc)

    if update.effective_message is not None:
        await update.effective_message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    elif update.effective_chat is not None:
        await update.effective_chat.send_message(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
