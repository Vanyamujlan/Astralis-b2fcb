"""Synastry compatibility engine comparing two real Swiss Ephemeris natal charts."""

from __future__ import annotations

from astralio.models.astrology import (
    CompatibilityReport,
    NatalChart,
    PlanetPosition,
    SynastryAspect,
)
from astralio.models.user import BirthData
from astralio.services.astrology_service import (
    MAJOR_ASPECTS,
    AstrologyService,
    angular_distance,
    longitude_to_sign,
)

# Element pair harmony scores (0..100 baseline contribution)
_ELEMENT_COMPAT: dict[frozenset[str], tuple[int, str]] = {
    frozenset({"Огонь"}): (82, "высокий общий темперамент и взаимный энтузиазм"),
    frozenset({"Земля"}): (84, "общий практичный взгляд на жизнь и устойчивость"),
    frozenset({"Воздух"}): (83, "лёгкое взаимопонимание, живой диалог и общие интересы"),
    frozenset({"Вода"}): (82, "тонкое эмоциональное созвучие и глубокая эмпатия"),
    frozenset({"Огонь", "Воздух"}): (86, "динамичный союз: идеи усиливают инициативу"),
    frozenset({"Земля", "Вода"}): (85, "тёплый и надёжный союз: забота сочетается с опорой"),
    frozenset({"Огонь", "Земля"}): (62, "разный темп жизни: импульс встречается с осторожностью"),
    frozenset({"Воздух", "Вода"}): (
        64,
        "рациональность и интуиция дополняют друг друга при уважении границ",
    ),
    frozenset({"Огонь", "Вода"}): (58, "сильные эмоции и яркий контраст темпераментов"),
    frozenset({"Земля", "Воздух"}): (
        60,
        "разные подходы к решениям: практика против экспериментов",
    ),
}

_SYNASTRY_KEYS = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn")


def _clamp(score: float) -> int:
    return max(20, min(98, int(round(score))))


def _aspect_explanation(
    key_a: str,
    key_b: str,
    name_a: str,
    name_b: str,
    aspect_ru: str,
    is_harmonious: bool,
) -> str:
    pair = {key_a, key_b}
    if pair == {"sun", "moon"}:
        return (
            f"{name_a} и {name_b} ({aspect_ru}): естественное ощущение «своего человека» и взаимной поддержки."
            if is_harmonious
            else f"{name_a} и {name_b} ({aspect_ru}): разный внутренний ритм требует бережного внимания к эмоциям партнёра."
        )
    if pair == {"venus", "mars"}:
        return (
            f"{name_a} и {name_b} ({aspect_ru}): яркое романтическое притяжение и живая химия."
            if is_harmonious
            else f"{name_a} и {name_b} ({aspect_ru}): сильная страсть, но важно не превращать искру в борьбу характеров."
        )
    if "mercury" in pair:
        return (
            f"{name_a} и {name_b} ({aspect_ru}): понятный диалог, схожий способ обсуждать планы и решения."
            if is_harmonious
            else f"{name_a} и {name_b} ({aspect_ru}): возможны недопонимания в формулировках — полезно проговаривать ожидания прямо."
        )
    if "saturn" in pair:
        return (
            f"{name_a} и {name_b} ({aspect_ru}): крепкий фундамент, чувство ответственности и перспектива на долгий срок."
            if is_harmonious
            else f"{name_a} и {name_b} ({aspect_ru}): проверка границ и зрелости — союз укрепляется через честные договорённости."
        )
    if "venus" in pair:
        return (
            f"{name_a} и {name_b} ({aspect_ru}): теплота, симпатия и схожее представление о заботе."
            if is_harmonious
            else f"{name_a} и {name_b} ({aspect_ru}): разные языки любви — важно открыто делиться тем, что дарит радость."
        )
    if "moon" in pair:
        return (
            f"{name_a} и {name_b} ({aspect_ru}): эмоциональный комфорт и интуитивное принятие друг друга."
            if is_harmonious
            else f"{name_a} и {name_b} ({aspect_ru}): повышенная эмоциональная чувствительность в острых темах."
        )
    return (
        f"{name_a} и {name_b} ({aspect_ru}): гармоничное усиление качеств в паре."
        if is_harmonious
        else f"{name_a} и {name_b} ({aspect_ru}): точка роста, требующая взаимной гибкости."
    )


class CompatibilityService:
    """Calculates synastry aspects and produces human-readable compatibility reports."""

    def __init__(self, astrology_service: AstrologyService) -> None:
        self._astrology = astrology_service

    def calculate_compatibility(
        self,
        *,
        person_a_name: str,
        person_a_birth: BirthData,
        person_b_name: str,
        person_b_birth: BirthData,
    ) -> CompatibilityReport:
        """Calculate synastry compatibility from two real BirthData inputs."""
        chart_a = self._astrology.calculate_natal_chart(person_a_birth, subject_name=person_a_name)
        chart_b = self._astrology.calculate_natal_chart(person_b_birth, subject_name=person_b_name)
        return self.compare_charts(chart_a, chart_b)

    def compare_charts(self, chart_a: NatalChart, chart_b: NatalChart) -> CompatibilityReport:
        """Compare two already-calculated NatalChart instances."""
        bodies_a: list[PlanetPosition] = [p for p in chart_a.planets if p.key in _SYNASTRY_KEYS]
        bodies_b: list[PlanetPosition] = [p for p in chart_b.planets if p.key in _SYNASTRY_KEYS]
        if chart_a.ascendant is not None and chart_b.ascendant is not None:
            bodies_a.append(chart_a.ascendant)
            bodies_b.append(chart_b.ascendant)

        synastry_aspects: list[SynastryAspect] = []
        emotional_delta = 0.0
        romance_delta = 0.0
        communication_delta = 0.0
        long_term_delta = 0.0

        for pa in bodies_a:
            for pb in bodies_b:
                dist = angular_distance(pa.longitude, pb.longitude)
                for asp_key, asp_ru, exact_angle, max_orb, is_harm in MAJOR_ASPECTS:
                    # Slightly tighter orb for synastry accuracy
                    allowed_orb = min(max_orb, 6.0)
                    orb = abs(dist - exact_angle)
                    if orb <= allowed_orb:
                        strength = 1.0 - (orb / allowed_orb) * 0.5
                        signed_weight = (8.5 if is_harm else -6.5) * strength
                        pair = {pa.key, pb.key}

                        if "moon" in pair:
                            emotional_delta += signed_weight * (
                                1.3 if "sun" in pair or pa.key == pb.key == "moon" else 0.9
                            )
                        if pair & {"venus", "mars"}:
                            romance_delta += signed_weight * (
                                1.3 if pair == {"venus", "mars"} else 0.85
                            )
                        if "mercury" in pair:
                            communication_delta += signed_weight * (
                                1.2 if pair == {"mercury"} else 0.85
                            )
                        if pair & {"saturn", "jupiter", "sun"}:
                            long_term_delta += signed_weight * (
                                1.1 if "saturn" in pair or "jupiter" in pair else 0.7
                            )

                        synastry_aspects.append(
                            SynastryAspect(
                                person_a_body=pa.name_ru,
                                person_b_body=pb.name_ru,
                                aspect_key=asp_key,
                                aspect_ru=asp_ru,
                                orb=round(orb, 2),
                                is_harmonious=is_harm,
                                summary=_aspect_explanation(
                                    pa.key,
                                    pb.key,
                                    f"{pa.name_ru} ({chart_a.subject_name})",
                                    f"{pb.name_ru} ({chart_b.subject_name})",
                                    asp_ru,
                                    is_harm,
                                ),
                            )
                        )
                        break

        synastry_aspects.sort(key=lambda a: a.orb)

        # Element compatibility baselines
        sun_a = next(p for p in chart_a.planets if p.key == "sun")
        sun_b = next(p for p in chart_b.planets if p.key == "sun")
        moon_a = next(p for p in chart_a.planets if p.key == "moon")
        moon_b = next(p for p in chart_b.planets if p.key == "moon")

        sun_el_a = longitude_to_sign(sun_a.longitude)[4]
        sun_el_b = longitude_to_sign(sun_b.longitude)[4]
        moon_el_a = longitude_to_sign(moon_a.longitude)[4]
        moon_el_b = longitude_to_sign(moon_b.longitude)[4]

        sun_base, sun_el_note = _ELEMENT_COMPAT[frozenset({sun_el_a, sun_el_b})]
        moon_base, moon_el_note = _ELEMENT_COMPAT[frozenset({moon_el_a, moon_el_b})]
        dom_base, _ = _ELEMENT_COMPAT[
            frozenset({chart_a.dominant_element, chart_b.dominant_element})
        ]

        emotional_score = _clamp(moon_base * 0.85 + 8 + emotional_delta)
        romance_score = _clamp((sun_base + dom_base) * 0.42 + 8 + romance_delta)
        communication_score = _clamp(dom_base * 0.85 + 8 + communication_delta)
        long_term_score = _clamp((sun_base + moon_base) * 0.42 + 8 + long_term_delta)
        overall_score = _clamp(
            emotional_score * 0.28
            + romance_score * 0.24
            + communication_score * 0.24
            + long_term_score * 0.24
        )

        strengths: list[str] = [
            f"Созвучие Солнц ({sun_a.sign_ru} + {sun_b.sign_ru}): {sun_el_note}."
        ]
        if moon_base >= 80:
            strengths.append(
                f"Эмоциональный фон ({moon_a.sign_ru} + {moon_b.sign_ru}): {moon_el_note}."
            )
        for asp in [a for a in synastry_aspects if a.is_harmonious][:3]:
            strengths.append(asp.summary)

        challenges: list[str] = []
        for asp in [a for a in synastry_aspects if not a.is_harmonious][:3]:
            challenges.append(asp.summary)
        if not challenges:
            challenges.append(
                "Явных напряжённых синастрических аспектов немного — важно осознанно поддерживать живой интерес и общие цели."
            )

        if overall_score >= 80:
            advice = (
                "У пары сильный природный резонанс. Берегите открытый диалог и не воспринимайте "
                "лёгкость взаимопонимания как должное — общие проекты и традиции сделают связь ещё глубже."
            )
        elif overall_score >= 65:
            advice = (
                "Гармоничный и перспективный союз с понятными точками роста. "
                "Если заранее проговаривать бытовые и эмоциональные ожидания, различия станут вашим преимуществом."
            )
        else:
            advice = (
                "Контрастная и яркая комбинация: партнёры смотрят на мир по-разному. "
                "Ключ к устойчивости — уважение к личному темпу друг друга, честные договорённости и готовность слышать."
            )

        limitations: list[str] = []
        if not chart_a.has_exact_time or not chart_b.has_exact_time:
            limitations.append(
                "У одного или обоих партнёров не указано точное время рождения: "
                "Асценденты и дома партнёров не участвовали в расчёте, а аспекты Луны ориентировочные."
            )

        return CompatibilityReport(
            person_a_name=chart_a.subject_name,
            person_b_name=chart_b.subject_name,
            chart_a=chart_a,
            chart_b=chart_b,
            overall_score=overall_score,
            emotional_score=emotional_score,
            romance_score=romance_score,
            communication_score=communication_score,
            long_term_score=long_term_score,
            synastry_aspects=synastry_aspects,
            strengths=strengths,
            challenges=challenges,
            advice=advice,
            limitations=limitations,
        )

    def format_compatibility_report(
        self,
        report: CompatibilityReport,
        extra_summary: str | None = None,
    ) -> str:
        """Render a clear, human-readable Russian compatibility report for Telegram."""
        sun_a = next(p for p in report.chart_a.planets if p.key == "sun")
        sun_b = next(p for p in report.chart_b.planets if p.key == "sun")
        moon_a = next(p for p in report.chart_a.planets if p.key == "moon")
        moon_b = next(p for p in report.chart_b.planets if p.key == "moon")

        lines = [
            f"💞 <b>Совместимость: {report.person_a_name} и {report.person_b_name}</b>",
            f"• {report.person_a_name}: ☉ {sun_a.sign_symbol} {sun_a.sign_ru}, ☽ {moon_a.sign_symbol} {moon_a.sign_ru}",
            f"• {report.person_b_name}: ☉ {sun_b.sign_symbol} {sun_b.sign_ru}, ☽ {moon_b.sign_symbol} {moon_b.sign_ru}",
            "",
            f"🌟 <b>Общая совместимость: {report.overall_score}%</b>",
            f"• Эмоциональная связь: {report.emotional_score}%",
            f"• Романтика и притяжение: {report.romance_score}%",
            f"• Общение и взаимопонимание: {report.communication_score}%",
            f"• Долгосрочный потенциал: {report.long_term_score}%",
            "",
            "<b>Сильные стороны союза:</b>",
        ]
        for item in report.strengths[:4]:
            lines.append(f"✦ {item}")

        lines.append("")
        lines.append("<b>На что обратить внимание:</b>")
        for item in report.challenges[:3]:
            lines.append(f"⚡ {item}")

        lines.extend(["", "<b>Рекомендация:</b>", extra_summary or report.advice])

        if report.limitations:
            lines.append("")
            lines.append("⚠️ <b>Ограничения расчёта:</b>")
            for lim in report.limitations:
                lines.append(f"• {lim}")

        return "\n".join(lines)
