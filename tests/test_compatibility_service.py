"""Tests for synastry compatibility calculation engine."""

from __future__ import annotations

from datetime import date, time

from astralio.models.user import BirthData
from astralio.services.astrology_service import AstrologyService
from astralio.services.compatibility_service import CompatibilityService


def test_compatibility_full_charts() -> None:
    astro = AstrologyService()
    compat = CompatibilityService(astro)

    person_a = BirthData(
        birth_date=date(1995, 5, 15),
        birth_time=time(14, 30),
        birth_place="Москва, Россия",
        latitude=55.7558,
        longitude=37.6173,
        timezone="Europe/Moscow",
    )
    person_b = BirthData(
        birth_date=date(1994, 9, 18),
        birth_time=time(10, 15),
        birth_place="Санкт-Петербург, Россия",
        latitude=59.9343,
        longitude=30.3351,
        timezone="Europe/Moscow",
    )

    report = compat.calculate_compatibility(
        person_a_name="Анна",
        person_a_birth=person_a,
        person_b_name="Дмитрий",
        person_b_birth=person_b,
    )

    assert 0 <= report.overall_score <= 100
    assert 0 <= report.emotional_score <= 100
    assert 0 <= report.romance_score <= 100
    assert 0 <= report.communication_score <= 100
    assert 0 <= report.long_term_score <= 100
    assert len(report.synastry_aspects) > 0
    assert len(report.strengths) > 0
    assert len(report.challenges) > 0
    assert report.advice
    assert report.limitations == []

    rendered = compat.format_compatibility_report(report)
    assert "Анна и Дмитрий" in rendered
    assert "Общая совместимость:" in rendered
    assert "Сильные стороны союза" in rendered


def test_compatibility_notes_limitations_when_time_unknown() -> None:
    astro = AstrologyService()
    compat = CompatibilityService(astro)

    person_a = BirthData(birth_date=date(1991, 3, 25), birth_time_unknown=True)
    person_b = BirthData(birth_date=date(1993, 7, 12), birth_time_unknown=True)

    report = compat.calculate_compatibility(
        person_a_name="Ольга",
        person_a_birth=person_a,
        person_b_name="Игорь",
        person_b_birth=person_b,
    )

    assert any("не указано точное время" in lim for lim in report.limitations)
    rendered = compat.format_compatibility_report(report)
    assert "Ограничения расчёта" in rendered
