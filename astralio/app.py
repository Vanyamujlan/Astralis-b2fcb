"""Application factory wiring Settings, Firestore repositories, Services, and PTB Application."""

from __future__ import annotations

from typing import Any

from telegram import BotCommand, Update
from telegram.ext import Application, ApplicationBuilder

from astralio.config import Settings
from astralio.handlers import register_all_handlers
from astralio.handlers.deps import SERVICES_BOT_DATA_KEY, ServiceContainer
from astralio.infrastructure.firebase import create_firestore_client
from astralio.infrastructure.geocoding import GeocodingService
from astralio.repositories.feedback_repository import FeedbackRepository
from astralio.repositories.payment_repository import PaymentRepository
from astralio.repositories.reading_repository import ReadingRepository
from astralio.repositories.user_repository import UserRepository
from astralio.services.ai_service import AIService
from astralio.services.astrology_service import AstrologyService
from astralio.services.compatibility_service import CompatibilityService
from astralio.services.forecast_service import ForecastService
from astralio.services.premium_service import PremiumService
from astralio.services.tarot_service import TarotService
from astralio.services.user_service import UserService


def build_service_container(
    settings: Settings,
    *,
    firestore_client: Any | None = None,
) -> ServiceContainer:
    """Instantiate repositories and services cleanly for production or tests."""
    db = firestore_client if firestore_client is not None else create_firestore_client(settings)

    user_repo = UserRepository(db)
    reading_repo = ReadingRepository(db)
    payment_repo = PaymentRepository(db)
    feedback_repo = FeedbackRepository(db)

    geocoding = GeocodingService(
        remote_enabled=settings.geocoding_enabled,
        timeout_seconds=settings.geocoding_timeout_seconds,
    )
    astrology = AstrologyService()
    compatibility = CompatibilityService(astrology)
    forecast = ForecastService(astrology)
    tarot = TarotService(reading_repo)
    premium = PremiumService(
        user_repo,
        payment_repo,
        telegram_stars_enabled=settings.telegram_stars_enabled,
    )
    ai_service = AIService(settings)
    user_service = UserService(user_repo, geocoding)

    return ServiceContainer(
        settings=settings,
        user_service=user_service,
        astrology_service=astrology,
        compatibility_service=compatibility,
        forecast_service=forecast,
        tarot_service=tarot,
        premium_service=premium,
        ai_service=ai_service,
        feedback_repository=feedback_repo,
    )


async def _post_init(app: Application) -> None:
    """Register clean Telegram bot commands menu on startup."""
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Запустить Astralio"),
            BotCommand("menu", "Открыть главное меню"),
            BotCommand("cancel", "Отменить текущее действие"),
        ]
    )


def build_application(
    settings: Settings,
    *,
    firestore_client: Any | None = None,
    services: ServiceContainer | None = None,
) -> Application:
    """Build a fully wired python-telegram-bot 22.x Application ready for polling."""
    container = services or build_service_container(settings, firestore_client=firestore_client)

    app = (
        ApplicationBuilder()
        .token(settings.bot_token.get_secret_value())
        .post_init(_post_init)
        .build()
    )
    app.bot_data[SERVICES_BOT_DATA_KEY] = container
    register_all_handlers(app)
    return app


ALLOWED_UPDATES: list[str] = [
    Update.MESSAGE,
    Update.CALLBACK_QUERY,
    Update.PRE_CHECKOUT_QUERY,
]
