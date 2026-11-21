"""Tests for Swiss Ephemeris natal chart calculations and input validators."""

from __future__ import annotations

from datetime import date, time

import pytest

from astralio.models.user import BirthData
from astralio.services.astrology_service import AstrologyService
from astralio.services.validators import (
    InputValidationError,
    parse_birth_date,
    parse_birth_time,
    parse_person_name,
    validate_feedback_text,
)


def test_natal_chart_full_precision_moscow() -> None:
    """Verify real Swiss Ephemeris calculation for a known date, time, and city."""
    service = AstrologyService()
    birth = BirthData(
        birth_date=date(1995, 5, 15),
        birth_time=time(14, 30),  # 14:30 Europe/Moscow (UTC+4 in summer 1995 -> 10:30 UTC)
        birth_time_unknown=False,
        birth_place="Москва, Россия",
        latitude=55.7558,
        longitude=37.6173,
        timezone="Europe/Moscow",
    )
    chart = service.calculate_natal_chart(birth, subject_name="Тест")

    assert chart.has_exact_time is True
    assert chart.has_coordinates is True
    assert len(chart.planets) == 10
    assert chart.ascendant is not None
    assert chart.midheaven is not None
    assert len(chart.houses) == 12
    assert chart.limitations == []

    by_key = {p.key: p for p in chart.planets}
    # May 15 is unambiguously in Taurus (~24 deg Taurus)
    assert by_key["sun"].sign_key == "taurus"
    assert 23.0 <= by_key["sun"].degree_in_sign <= 25.0
    # Every planet must have a house assignment 1..12 when houses are computed
    assert all(p.house is not None and 1 <= p.house <= 12 for p in chart.planets)
    # Natal chart message contains key sections
    rendered = service.format_natal_chart(chart)
    assert "Swiss Ephemeris" in rendered
    assert "Телец" in rendered
    assert "Асцендент" in rendered


def test_natal_chart_unknown_time_reports_limitations() -> None:
    """When birth time is unknown, Ascendant/houses must not be fabricated and limitations must be stated."""
    service = AstrologyService()
    birth = BirthData(
        birth_date=date(1990, 1, 10),
        birth_time=None,
        birth_time_unknown=True,
        birth_place="Москва, Россия",
        latitude=55.7558,
        longitude=37.6173,
        timezone="Europe/Moscow",
    )
    chart = service.calculate_natal_chart(birth, subject_name="Алексей")

    assert chart.has_exact_time is False
    assert chart.ascendant is None
    assert chart.midheaven is None
    assert chart.houses == []
    assert all(p.house is None for p in chart.planets)
    assert any("Точное время рождения не указано" in item for item in chart.limitations)

    by_key = {p.key: p for p in chart.planets}
    assert by_key["sun"].sign_key == "capricorn"


def test_natal_chart_missing_coordinates_reports_limitations() -> None:
    service = AstrologyService()
    birth = BirthData(
        birth_date=date(1992, 8, 5),
        birth_time=time(9, 15),
        birth_time_unknown=False,
    )
    chart = service.calculate_natal_chart(birth)

    assert chart.ascendant is None
    assert chart.houses == []
    assert any("Координаты места рождения" in item for item in chart.limitations)


def test_natal_chart_polar_latitude_uses_whole_sign_houses() -> None:
    """Above 66 degrees latitude Placidus is degenerate; engine falls back to Whole Sign."""
    service = AstrologyService()
    birth = BirthData(
        birth_date=date(1998, 12, 1),
        birth_time=time(16, 0),
        birth_time_unknown=False,
        birth_place="Мурманск, Россия",
        latitude=68.9585,
        longitude=33.0827,
        timezone="Europe/Moscow",
    )
    chart = service.calculate_natal_chart(birth)

    assert chart.ascendant is not None
    assert len(chart.houses) == 12
    assert any("полнознаковая" in item for item in chart.limitations)


def test_birth_date_validator() -> None:
    ref_today = date(2026, 11, 21)
    assert parse_birth_date("15.05.1995", today=ref_today) == date(1995, 5, 15)
    assert parse_birth_date("1995-05-15", today=ref_today) == date(1995, 5, 15)

    for bad in ["", "99.99.1995", "31.02.2000", "15.05.1890", "01.01.2035", "abc"]:
        with pytest.raises(InputValidationError):
            parse_birth_date(bad, today=ref_today)


def test_birth_time_validator() -> None:
    assert parse_birth_time("09:45") == (time(9, 45), False)
    assert parse_birth_time("23:59") == (time(23, 59), False)
    assert parse_birth_time("неизвестно") == (None, True)
    assert parse_birth_time("не знаю") == (None, True)

    for bad in ["", "25:00", "12:60", "abc", "9"]:
        with pytest.raises(InputValidationError):
            parse_birth_time(bad)


def test_name_and_feedback_validators() -> None:
    assert parse_person_name("  Иван   Петров ") == "Иван Петров"
    with pytest.raises(InputValidationError):
        parse_person_name("А")
    with pytest.raises(InputValidationError):
        parse_person_name("/start")

    assert validate_feedback_text("Отличный бот!") == "Отличный бот!"
    with pytest.raises(InputValidationError):
        validate_feedback_text("ок")
