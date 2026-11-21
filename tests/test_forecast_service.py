"""Tests for personalized transit-based daily and weekly forecasts."""

from __future__ import annotations

from datetime import date, time

from astralio.models.astrology import ForecastPeriod
from astralio.models.user import BirthData
from astralio.services.astrology_service import AstrologyService
from astralio.services.forecast_service import ForecastService


def test_daily_and_weekly_forecasts_are_personalized_by_natal_chart() -> None:
    astro = AstrologyService()
    forecast = ForecastService(astro)
    ref_day = date(2026, 11, 21)

    birth_taurus = BirthData(
        birth_date=date(1995, 5, 15),
        birth_time=time(14, 30),
        birth_place="Москва, Россия",
        latitude=55.7558,
        longitude=37.6173,
        timezone="Europe/Moscow",
    )
    birth_sag = BirthData(
        birth_date=date(1988, 12, 5),
        birth_time=time(6, 20),
        birth_place="Алматы, Казахстан",
        latitude=43.2389,
        longitude=76.8897,
        timezone="Asia/Almaty",
    )

    daily_a = forecast.generate_forecast(
        birth_taurus,
        period=ForecastPeriod.DAILY,
        reference_date=ref_day,
    )
    daily_b = forecast.generate_forecast(
        birth_sag,
        period=ForecastPeriod.DAILY,
        reference_date=ref_day,
    )
    weekly_a = forecast.generate_forecast(
        birth_taurus,
        period=ForecastPeriod.WEEKLY,
        reference_date=ref_day,
    )

    assert daily_a.sun_sign_ru == "Телец"
    assert daily_b.sun_sign_ru == "Стрелец"
    assert daily_a.start_date == daily_a.end_date == ref_day
    assert (weekly_a.end_date - weekly_a.start_date).days == 6

    # Forecasts must differ meaningfully based on actual calculated natal positions
    assert (
        daily_a.key_themes != daily_b.key_themes
        or daily_a.active_transits != daily_b.active_transits
    )

    rendered_daily = forecast.format_forecast(daily_a)
    rendered_weekly = forecast.format_forecast(weekly_a)
    assert "Персональный прогноз на 21.11.2026" in rendered_daily
    assert "Персональный прогноз на неделю" in rendered_weekly


def test_forecast_propagates_unknown_time_limitations() -> None:
    astro = AstrologyService()
    forecast = ForecastService(astro)
    birth = BirthData(birth_date=date(1992, 4, 10), birth_time_unknown=True)

    report = forecast.generate_forecast(
        birth,
        period=ForecastPeriod.DAILY,
        reference_date=date(2026, 11, 21),
    )
    assert report.limitations
    rendered = forecast.format_forecast(report)
    assert "Примечание по точности" in rendered
