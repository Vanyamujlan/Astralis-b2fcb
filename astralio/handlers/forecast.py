"""Personalized daily and weekly transit forecast handlers."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from astralio.handlers.deps import ensure_user, escape_html, get_services, reply_or_edit
from astralio.keyboards.callbacks import CB
from astralio.keyboards.menus import forecast_menu_keyboard
from astralio.models.astrology import ForecastPeriod


async def show_forecast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the Forecast section menu."""
    profile = await ensure_user(update, context)
    has_date = profile.birth_data.has_birth_date
    intro = (
        "Прогнозы рассчитываются по реальным текущим транзитам планет к вашей натальной карте."
        if has_date
        else (
            "Для персонального прогноза по транзитам сначала заполните дату рождения в профиле "
            "или через «Натальную карту» — мы не подменяем персональный расчёт общими текстами."
        )
    )
    await reply_or_edit(
        update,
        f"🔮 <b>Персональные прогнозы</b>\n\n{intro}",
        reply_markup=forecast_menu_keyboard(has_saved_birth_date=has_date),
    )


async def _handle_forecast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    period: ForecastPeriod,
) -> None:
    profile = await ensure_user(update, context)
    if not profile.birth_data.has_birth_date:
        await reply_or_edit(
            update,
            "⚠️ <b>Недостаточно данных для персонального прогноза</b>\n\n"
            "Чтобы рассчитать транзиты именно к вашей натальной карте, укажите дату рождения "
            "(а для большей точности — время и место).",
            reply_markup=forecast_menu_keyboard(has_saved_birth_date=False),
        )
        return

    services = get_services(context)
    report = services.forecast_service.generate_forecast(
        profile.birth_data,
        period=period,
        subject_name=profile.display_name,
    )

    extra_summary: str | None = None
    if services.ai_service.is_enabled and report.active_transits:
        facts = "; ".join(
            f"{ev.transit_planet} {ev.aspect_ru} натал. {ev.natal_planet} (орб {ev.orb:.1f}°)"
            for ev in report.active_transits
        )
        period_ru = "день" if period == ForecastPeriod.DAILY else "неделю"
        ai_res = await services.ai_service.enhance_interpretation(
            user_id=profile.telegram_id,
            system_prompt=(
                f"Ты астролог-аналитик. Напиши краткую персональную сводку на {period_ru} (3-4 предложения) "
                "на русском языке строго по переданным активным транзитам."
            ),
            facts_prompt=f"Натальное Солнце: {report.sun_sign_ru}, Луна: {report.moon_sign_ru}. Транзиты: {facts}.",
            local_fallback="",
        )
        if ai_res.source == "ai" and ai_res.text:
            extra_summary = escape_html(ai_res.text)

    text = services.forecast_service.format_forecast(report, extra_summary=extra_summary)
    await reply_or_edit(
        update,
        text,
        reply_markup=forecast_menu_keyboard(has_saved_birth_date=True),
    )


async def show_daily_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_forecast(update, context, ForecastPeriod.DAILY)


async def show_weekly_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_forecast(update, context, ForecastPeriod.WEEKLY)


def register_forecast_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(show_forecast_menu, pattern=f"^{CB.MENU_FORECAST}$"))
    app.add_handler(CallbackQueryHandler(show_daily_forecast, pattern=f"^{CB.FORECAST_DAILY}$"))
    app.add_handler(CallbackQueryHandler(show_weekly_forecast, pattern=f"^{CB.FORECAST_WEEKLY}$"))
