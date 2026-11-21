"""Personalized daily and weekly transit forecasts based on real ephemeris positions."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from astralio.models.astrology import (
    ForecastPeriod,
    ForecastReport,
    NatalChart,
    PlanetPosition,
    TransitEvent,
)
from astralio.models.user import BirthData
from astralio.services.astrology_service import (
    MAJOR_ASPECTS,
    AstrologyService,
    angular_distance,
)

# Transit planetary themes for concrete, non-generic transit guidance
_TRANSIT_THEMES: dict[str, tuple[str, str, str]] = {
    "sun": (
        "фокус внимания и жизненная энергия",
        "удачное время для проявления инициативы и ясных шагов",
        "избегайте перегрузки и действуйте без спешки",
    ),
    "moon": (
        "эмоциональный фон и интуиция",
        "прислушивайтесь к ощущениям — они подскажут верный ритм дня",
        "не принимайте резких решений на эмоциях, дайте себе паузу",
    ),
    "mercury": (
        "переговоры, документы и ясность ума",
        "хороший момент для переписки, обучения и важных обсуждений",
        "перепроверяйте детали и уточняйте договорённости письменно",
    ),
    "venus": (
        "отношения, симпатии и финансовый комфорт",
        "благоприятно для встреч, творчества и заботы о себе",
        "избегайте импульсивных трат и обид из-за недосказанности",
    ),
    "mars": (
        "активность, смелость и отстаивание границ",
        "направьте энергию в конкретные задачи и спорт",
        "снизьте градус споров — энергию лучше пустить в дело, а не в конфликт",
    ),
    "jupiter": (
        "расширение горизонтов и возможности роста",
        "открывайтесь новым предложениям и долгосрочным идеям",
        "не давайте завышенных обещаний, оценивайте ресурсы реалистично",
    ),
    "saturn": (
        "структура, ответственность и зрелые решения",
        "укрепляйте дисциплину и доводите начатые проекты до результата",
        "не давите на себя жёсткой критикой — двигайтесь системно, шаг за шагом",
    ),
}

_NATAL_TARGETS = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn")


class ForecastService:
    """Computes genuine transit-to-natal daily and weekly forecasts using Swiss Ephemeris."""

    def __init__(self, astrology_service: AstrologyService) -> None:
        self._astrology = astrology_service

    def generate_forecast(
        self,
        birth_data: BirthData,
        *,
        period: ForecastPeriod,
        subject_name: str = "Пользователь",
        reference_date: date | None = None,
    ) -> ForecastReport:
        """Compute active transits against the user's real natal chart."""
        chart = self._astrology.calculate_natal_chart(birth_data, subject_name=subject_name)
        return self.generate_forecast_from_chart(
            chart,
            period=period,
            reference_date=reference_date,
        )

    def generate_forecast_from_chart(
        self,
        chart: NatalChart,
        *,
        period: ForecastPeriod,
        reference_date: date | None = None,
    ) -> ForecastReport:
        """Compute daily (1 day) or weekly (7 days) transit report for a NatalChart."""
        start = reference_date or datetime.now(UTC).date()
        days_count = 1 if period == ForecastPeriod.DAILY else 7
        end = start + timedelta(days=days_count - 1)

        natal_targets: list[PlanetPosition] = [p for p in chart.planets if p.key in _NATAL_TARGETS]
        if chart.ascendant is not None:
            natal_targets.append(chart.ascendant)

        # Deduplicate transits across the weekly window keeping the tightest orb
        best_transits: dict[tuple[str, str, str], TransitEvent] = {}

        for offset in range(days_count):
            day = start + timedelta(days=offset)
            noon_utc = datetime(day.year, day.month, day.day, 12, 0, 0, tzinfo=UTC)
            transit_planets = self._astrology.calculate_planet_positions(noon_utc)

            for tr in transit_planets:
                if tr.key not in _TRANSIT_THEMES:
                    continue
                # For weekly view skip fast-moving Moon noise unless very exact
                orb_limit = 2.5 if (period == ForecastPeriod.WEEKLY and tr.key == "moon") else 4.0

                for natal in natal_targets:
                    dist = angular_distance(tr.longitude, natal.longitude)
                    for asp_key, asp_ru, exact_angle, _default_orb, is_harm in MAJOR_ASPECTS:
                        orb = abs(dist - exact_angle)
                        if orb <= orb_limit:
                            theme_name, harm_tip, tense_tip = _TRANSIT_THEMES[tr.key]
                            guidance = harm_tip if is_harm else tense_tip
                            dedup_key = (tr.key, natal.key, asp_key)
                            event = TransitEvent(
                                transit_date=day,
                                transit_planet=tr.name_ru,
                                natal_planet=natal.name_ru,
                                aspect_key=asp_key,
                                aspect_ru=asp_ru,
                                orb=round(orb, 2),
                                is_harmonious=is_harm,
                                theme=theme_name,
                                guidance=guidance,
                            )
                            existing = best_transits.get(dedup_key)
                            if existing is None or event.orb < existing.orb:
                                best_transits[dedup_key] = event
                            break

        sorted_events = sorted(best_transits.values(), key=lambda e: (e.orb, e.transit_date))
        selected = sorted_events[: (5 if period == ForecastPeriod.DAILY else 7)]

        sun = next(p for p in chart.planets if p.key == "sun")
        moon = next(p for p in chart.planets if p.key == "moon")

        key_themes: list[str] = []
        practical_advice: list[str] = []

        if selected:
            seen_themes: set[str] = set()
            seen_advice: set[str] = set()
            for ev in selected:
                if ev.theme not in seen_themes:
                    seen_themes.add(ev.theme)
                    key_themes.append(
                        f"{ev.transit_planet} ({ev.aspect_ru.lower()} к натальному {ev.natal_planet}): {ev.theme}"
                    )
                if ev.guidance not in seen_advice:
                    seen_advice.add(ev.guidance)
                    practical_advice.append(ev.guidance.capitalize() + ".")
        else:
            # Calm background transits — explicitly state real quiet sky instead of inventing drama
            noon_start = datetime(start.year, start.month, start.day, 12, 0, 0, tzinfo=UTC)
            current_planets = {
                p.key: p for p in self._astrology.calculate_planet_positions(noon_start)
            }
            tr_sun = current_planets["sun"]
            tr_moon = current_planets["moon"]
            key_themes.append(
                f"Спокойный транзитный фон без жёстких точных аспектов к натальной карте "
                f"(транзитное Солнце в знаке {tr_sun.sign_ru}, Луна в знаке {tr_moon.sign_ru})."
            )
            practical_advice.append(
                "Подходящее время для спокойного продолжения текущих задач без внешнего давления."
            )

        limitations = list(chart.limitations)
        return ForecastReport(
            period=period,
            start_date=start,
            end_date=end,
            sun_sign_ru=sun.sign_ru,
            moon_sign_ru=moon.sign_ru,
            active_transits=selected,
            key_themes=key_themes[:4],
            practical_advice=practical_advice[:4],
            limitations=limitations,
            interpretation_source="local",
        )

    def format_forecast(
        self,
        report: ForecastReport,
        extra_summary: str | None = None,
    ) -> str:
        """Render a personalized forecast as clean HTML for Telegram."""
        if report.period == ForecastPeriod.DAILY:
            header = f"🌅 <b>Персональный прогноз на {report.start_date.strftime('%d.%m.%Y')}</b>"
        else:
            header = (
                f"🗓 <b>Персональный прогноз на неделю "
                f"({report.start_date.strftime('%d.%m')} — {report.end_date.strftime('%d.%m.%Y')})</b>"
            )

        lines = [
            header,
            f"Натальная база: ☉ {report.sun_sign_ru} | ☽ {report.moon_sign_ru}",
            "",
        ]

        if report.active_transits:
            lines.append("<b>Активные транзиты к вашей карте:</b>")
            for ev in report.active_transits:
                icon = "✦" if ev.is_harmonious else "⚡"
                date_tag = (
                    f"[{ev.transit_date.strftime('%d.%m')}] "
                    if report.period == ForecastPeriod.WEEKLY
                    else ""
                )
                lines.append(
                    f"{icon} {date_tag}{ev.transit_planet} — {ev.aspect_ru} — "
                    f"натал. {ev.natal_planet} (орб {ev.orb:.1f}°)"
                )
            lines.append("")

        lines.append("<b>Ключевые акценты:</b>")
        for theme in report.key_themes:
            lines.append(f"• {theme}")

        lines.append("")
        lines.append("<b>Практические рекомендации:</b>")
        for tip in report.practical_advice:
            lines.append(f"• {tip}")

        if extra_summary:
            lines.extend(["", "<b>Развёрнутая сводка:</b>", extra_summary])

        if report.limitations:
            lines.append("")
            lines.append("⚠️ <b>Примечание по точности:</b>")
            for lim in report.limitations:
                lines.append(f"• {lim}")

        return "\n".join(lines)
