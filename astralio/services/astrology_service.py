"""Real astronomical natal chart calculations powered by Swiss Ephemeris (pyswisseph)."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import swisseph as swe

from astralio.models.astrology import Aspect, HouseCusp, NatalChart, PlanetPosition
from astralio.models.user import BirthData

# Zodiac sign metadata: (key, Russian name, glyph, element, modality)
ZODIAC_SIGNS: tuple[tuple[str, str, str, str, str], ...] = (
    ("aries", "Овен", "♈", "Огонь", "Кардинальный"),
    ("taurus", "Телец", "♉", "Земля", "Фиксированный"),
    ("gemini", "Близнецы", "♊", "Воздух", "Мутабельный"),
    ("cancer", "Рак", "♋", "Вода", "Кардинальный"),
    ("leo", "Лев", "♌", "Огонь", "Фиксированный"),
    ("virgo", "Дева", "♍", "Земля", "Мутабельный"),
    ("libra", "Весы", "♎", "Воздух", "Кардинальный"),
    ("scorpio", "Скорпион", "♏", "Вода", "Фиксированный"),
    ("sagittarius", "Стрелец", "♐", "Огонь", "Мутабельный"),
    ("capricorn", "Козерог", "♑", "Земля", "Кардинальный"),
    ("aquarius", "Водолей", "♒", "Воздух", "Фиксированный"),
    ("pisces", "Рыбы", "♓", "Вода", "Мутабельный"),
)

# Planets computed via Swiss Ephemeris Moshier ephemeris
PLANET_SPECS: tuple[tuple[int, str, str, str], ...] = (
    (swe.SUN, "sun", "Солнце", "☉"),
    (swe.MOON, "moon", "Луна", "☽"),
    (swe.MERCURY, "mercury", "Меркурий", "☿"),
    (swe.VENUS, "venus", "Венера", "♀"),
    (swe.MARS, "mars", "Марс", "♂"),
    (swe.JUPITER, "jupiter", "Юпитер", "♃"),
    (swe.SATURN, "saturn", "Сатурн", "♄"),
    (swe.URANUS, "uranus", "Уран", "♅"),
    (swe.NEPTUNE, "neptune", "Нептун", "♆"),
    (swe.PLUTO, "pluto", "Плутон", "♇"),
)

# Major Ptolemaic aspects: (key, Russian name, exact angle, max orb, is_harmonious)
MAJOR_ASPECTS: tuple[tuple[str, str, float, float, bool], ...] = (
    ("conjunction", "Соединение", 0.0, 8.0, True),
    ("sextile", "Секстиль", 60.0, 5.0, True),
    ("square", "Квадрат", 90.0, 6.0, False),
    ("trine", "Трин", 120.0, 7.0, True),
    ("opposition", "Оппозиция", 180.0, 7.0, False),
)

SUN_SIGN_DESCRIPTIONS: dict[str, str] = {
    "aries": "инициативность, прямота, внутренняя энергия первопроходца",
    "taurus": "устойчивость, практичность, стремление к надёжности и комфорту",
    "gemini": "любознательность, гибкость мышления, тяга к общению и новым идеям",
    "cancer": "глубокая чувствительность, забота о близких, сильная интуиция",
    "leo": "выразительность, щедрость, стремление к творческому самовыражению",
    "virgo": "внимательность к деталям, системность, стремление к порядку и пользе",
    "libra": "дипломатичность, чувство баланса, ориентация на партнёрство и эстетику",
    "scorpio": "интенсивность переживаний, проницательность, способность к трансформации",
    "sagittarius": "стремление к росту, широта взглядов, поиск смысла и свободы",
    "capricorn": "целеустремлённость, дисциплина, стратегический подход к жизни",
    "aquarius": "независимость, оригинальность мышления, интерес к будущему и сообществам",
    "pisces": "эмпатия, богатая фантазия, тонкое восприятие скрытых смыслов",
}

MOON_SIGN_DESCRIPTIONS: dict[str, str] = {
    "aries": "эмоциональные реакции быстрые и искренние, важна личная автономия",
    "taurus": "внутреннее спокойствие строится через стабильность, привычный ритм и телесный комфорт",
    "gemini": "эмоции проживаются через осмысление, диалог и обмен впечатлениями",
    "cancer": "сильная привязанность к дому, эмоциональная память и потребность в безопасности",
    "leo": "потребность в тёплом признании, искренней лояльности и вдохновении",
    "virgo": "спокойствие приходит через ясность, полезные дела и заботу в мелочах",
    "libra": "эмоциональный баланс зависит от гармонии в отношениях и мягкой атмосферы",
    "scorpio": "глубокие и устойчивые чувства, высокая чувствительность к искренности",
    "sagittarius": "эмоциональное восстановление через смену впечатлений, обучение и перспективу",
    "capricorn": "сдержанность в проявлении чувств, опора на ответственность и внутренний стержень",
    "aquarius": "потребность в эмоциональной свободе, уважении границ и дружеской поддержке",
    "pisces": "тонкая интуиция, сопереживание и необходимость регулярного уединения для отдыха",
}

ELEMENT_DESCRIPTIONS: dict[str, str] = {
    "Огонь": "Преобладает стихия Огня — высокая жизненная динамика, мотивация к действию и лидерству.",
    "Земля": "Преобладает стихия Земли — опора на факты, последовательность и материальный результат.",
    "Воздух": "Преобладает стихия Воздуха — сильный интеллект, коммуникабельность и умение видеть связи.",
    "Вода": "Преобладает стихия Воды — развитая эмпатия, интуитивность и глубина эмоционального мира.",
}


def longitude_to_sign(longitude: float) -> tuple[str, str, str, float, str, str]:
    """Convert ecliptic longitude [0, 360) to zodiac sign metadata and degree within sign."""
    normalized = longitude % 360.0
    sign_index = int(normalized // 30.0) % 12
    degree_in_sign = normalized - sign_index * 30.0
    key, name_ru, symbol, element, modality = ZODIAC_SIGNS[sign_index]
    return key, name_ru, symbol, degree_in_sign, element, modality


def angular_distance(lon_a: float, lon_b: float) -> float:
    """Shortest angular separation [0, 180] between two ecliptic longitudes."""
    diff = abs((lon_a - lon_b) % 360.0)
    return 360.0 - diff if diff > 180.0 else diff


def _find_house_for_longitude(longitude: float, cusps: list[float]) -> int:
    """Determine astrological house (1..12) for an ecliptic longitude given 12 house cusps."""
    lon = longitude % 360.0
    for idx in range(12):
        start = cusps[idx] % 360.0
        end = cusps[(idx + 1) % 12] % 360.0
        if start <= end:
            if start <= lon < end:
                return idx + 1
        elif lon >= start or lon < end:
            return idx + 1
    return 1


def _format_deg_min(degree: float) -> str:
    whole = int(degree)
    minutes = int(round((degree - whole) * 60))
    if minutes == 60:
        whole += 1
        minutes = 0
    return f"{whole:02d}°{minutes:02d}′"


class AstrologyService:
    """Performs real ephemeris calculations using Swiss Ephemeris (Moshier mode)."""

    _CALC_FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED

    def to_julian_day(self, dt_utc: datetime) -> float:
        """Convert timezone-aware UTC datetime to Julian Day (UT)."""
        utc = dt_utc.astimezone(UTC) if dt_utc.tzinfo is not None else dt_utc.replace(tzinfo=UTC)
        decimal_hour = utc.hour + utc.minute / 60.0 + utc.second / 3600.0
        return float(swe.julday(utc.year, utc.month, utc.day, decimal_hour))

    def calculate_planet_positions(self, dt_utc: datetime) -> list[PlanetPosition]:
        """Compute exact ecliptic positions of Sun through Pluto for any UTC moment."""
        jd = self.to_julian_day(dt_utc)
        positions: list[PlanetPosition] = []
        for body_id, key, name_ru, symbol in PLANET_SPECS:
            values, _flags = swe.calc_ut(jd, body_id, self._CALC_FLAGS)
            lon = float(values[0]) % 360.0
            speed = float(values[3])
            sign_key, sign_ru, sign_symbol, deg, _el, _mod = longitude_to_sign(lon)
            positions.append(
                PlanetPosition(
                    key=key,
                    name_ru=name_ru,
                    symbol=symbol,
                    longitude=round(lon, 4),
                    sign_key=sign_key,
                    sign_ru=sign_ru,
                    sign_symbol=sign_symbol,
                    degree_in_sign=round(deg, 4),
                    speed=round(speed, 5),
                    is_retrograde=speed < 0.0 and key not in {"sun", "moon"},
                )
            )
        return positions

    def _resolve_utc_datetime(
        self,
        birth_date: date,
        birth_time: time | None,
        birth_time_unknown: bool,
        tz_name: str | None,
    ) -> tuple[datetime, list[str]]:
        limitations: list[str] = []
        if birth_time is None or birth_time_unknown:
            dt_utc = datetime(
                birth_date.year,
                birth_date.month,
                birth_date.day,
                12,
                0,
                0,
                tzinfo=UTC,
            )
            limitations.append(
                "Точное время рождения не указано: расчёт выполнен на 12:00 UTC. "
                "Асцендент, Середина Неба и дома не рассчитаны, а положение Луны "
                "может отличаться в пределах ±6°."
            )
            return dt_utc, limitations

        if tz_name:
            try:
                tz = ZoneInfo(tz_name)
                local_dt = datetime.combine(birth_date, birth_time, tzinfo=tz)
                return local_dt.astimezone(UTC), limitations
            except ZoneInfoNotFoundError:
                limitations.append(
                    f"Часовой пояс «{tz_name}» не найден; время рождения интерпретировано как UTC."
                )
        else:
            limitations.append(
                "Часовой пояс места рождения не определён; время рождения интерпретировано как UTC."
            )

        return datetime.combine(birth_date, birth_time, tzinfo=UTC), limitations

    def calculate_natal_chart(
        self,
        birth_data: BirthData,
        *,
        subject_name: str = "Пользователь",
    ) -> NatalChart:
        """Calculate a full natal chart from BirthData using Swiss Ephemeris."""
        if birth_data.birth_date is None:
            raise ValueError("Для расчёта натальной карты необходима дата рождения.")

        dt_utc, limitations = self._resolve_utc_datetime(
            birth_data.birth_date,
            birth_data.birth_time,
            birth_data.birth_time_unknown,
            birth_data.timezone,
        )
        jd = self.to_julian_day(dt_utc)
        planets = self.calculate_planet_positions(dt_utc)

        ascendant: PlanetPosition | None = None
        midheaven: PlanetPosition | None = None
        houses: list[HouseCusp] = []

        can_calculate_houses = birth_data.has_exact_time and birth_data.has_coordinates
        if birth_data.has_exact_time and not birth_data.has_coordinates:
            limitations.append(
                "Координаты места рождения не указаны: Асцендент, Середина Неба и дома не рассчитаны."
            )

        if can_calculate_houses:
            assert birth_data.latitude is not None and birth_data.longitude is not None
            house_system = b"P"
            if abs(birth_data.latitude) >= 66.0:
                house_system = b"W"
                limitations.append(
                    "Широта рождения выше 66°: вместо системы Плацидуса применена полнознаковая система домов."
                )
            cusps_raw, ascmc = swe.houses(
                jd, birth_data.latitude, birth_data.longitude, house_system
            )
            cusp_lons = [float(c) % 360.0 for c in cusps_raw[:12]]

            asc_lon = float(ascmc[0]) % 360.0
            mc_lon = float(ascmc[1]) % 360.0

            asc_key, asc_ru, asc_sym, asc_deg, _, _ = longitude_to_sign(asc_lon)
            ascendant = PlanetPosition(
                key="ascendant",
                name_ru="Асцендент (ASC)",
                symbol="ASC",
                longitude=round(asc_lon, 4),
                sign_key=asc_key,
                sign_ru=asc_ru,
                sign_symbol=asc_sym,
                degree_in_sign=round(asc_deg, 4),
                house=1,
            )

            mc_key, mc_ru, mc_sym, mc_deg, _, _ = longitude_to_sign(mc_lon)
            midheaven = PlanetPosition(
                key="midheaven",
                name_ru="Середина Неба (MC)",
                symbol="MC",
                longitude=round(mc_lon, 4),
                sign_key=mc_key,
                sign_ru=mc_ru,
                sign_symbol=mc_sym,
                degree_in_sign=round(mc_deg, 4),
                house=10,
            )

            for idx, cusp_lon in enumerate(cusp_lons, start=1):
                c_key, c_ru, c_sym, c_deg, _, _ = longitude_to_sign(cusp_lon)
                houses.append(
                    HouseCusp(
                        number=idx,
                        longitude=round(cusp_lon, 4),
                        sign_key=c_key,
                        sign_ru=c_ru,
                        sign_symbol=c_sym,
                        degree_in_sign=round(c_deg, 4),
                    )
                )

            for planet in planets:
                planet.house = _find_house_for_longitude(planet.longitude, cusp_lons)

        aspects = self._calculate_natal_aspects(planets, ascendant)

        # Compute dominant element across personal & social planets (with extra weight for Sun/Moon)
        element_counts: Counter[str] = Counter()
        for planet in planets:
            _, _, _, _, element, _ = longitude_to_sign(planet.longitude)
            weight = 2 if planet.key in {"sun", "moon"} else 1
            element_counts[element] += weight
        if ascendant is not None:
            _, _, _, _, asc_el, _ = longitude_to_sign(ascendant.longitude)
            element_counts[asc_el] += 2
        dominant_element = element_counts.most_common(1)[0][0]

        return NatalChart(
            subject_name=subject_name,
            birth_date=birth_data.birth_date,
            birth_time_str=birth_data.birth_time.strftime("%H:%M")
            if birth_data.has_exact_time and birth_data.birth_time
            else None,
            birth_place=birth_data.birth_place,
            calculated_utc=dt_utc,
            julian_day=round(jd, 6),
            has_exact_time=birth_data.has_exact_time,
            has_coordinates=birth_data.has_coordinates,
            planets=planets,
            ascendant=ascendant,
            midheaven=midheaven,
            houses=houses,
            aspects=aspects,
            dominant_element=dominant_element,
            limitations=limitations,
        )

    def _calculate_natal_aspects(
        self,
        planets: list[PlanetPosition],
        ascendant: PlanetPosition | None,
    ) -> list[Aspect]:
        bodies = list(planets)
        if ascendant is not None:
            bodies.append(ascendant)

        found: list[Aspect] = []
        for i in range(len(bodies)):
            for j in range(i + 1, len(bodies)):
                body_a = bodies[i]
                body_b = bodies[j]
                dist = angular_distance(body_a.longitude, body_b.longitude)
                for asp_key, asp_ru, exact_angle, max_orb, is_harm in MAJOR_ASPECTS:
                    orb = abs(dist - exact_angle)
                    if orb <= max_orb:
                        found.append(
                            Aspect(
                                body_a=body_a.name_ru,
                                body_b=body_b.name_ru,
                                aspect_key=asp_key,
                                aspect_ru=asp_ru,
                                angle=exact_angle,
                                orb=round(orb, 2),
                                is_harmonious=is_harm,
                            )
                        )
                        break

        found.sort(key=lambda a: a.orb)
        return found

    def build_local_interpretation(self, chart: NatalChart) -> str:
        """Generate a grounded, non-fabricated Russian interpretation of a NatalChart."""
        by_key = {p.key: p for p in chart.planets}
        sun = by_key["sun"]
        moon = by_key["moon"]

        parts = [
            f"• <b>Солнце в знаке {sun.sign_ru}</b>: {SUN_SIGN_DESCRIPTIONS[sun.sign_key]}.",
            f"• <b>Луна в знаке {moon.sign_ru}</b>: {MOON_SIGN_DESCRIPTIONS[moon.sign_key]}.",
        ]
        if chart.ascendant is not None:
            parts.append(
                f"• <b>Асцендент в знаке {chart.ascendant.sign_ru}</b>: "
                f"первое впечатление и стиль взаимодействия с миром окрашены качествами знака {chart.ascendant.sign_ru}."
            )
        parts.append(f"• <b>Стихия карты</b>: {ELEMENT_DESCRIPTIONS[chart.dominant_element]}")

        retrogrades = [p.name_ru for p in chart.planets if p.is_retrograde]
        if retrogrades:
            parts.append(
                f"• <b>Ретроградные планеты</b> ({', '.join(retrogrades)}): "
                "темы этих планет раскрываются глубже через внутренний пересмотр и личный опыт."
            )
        return "\n".join(parts)

    def format_natal_chart(self, chart: NatalChart, interpretation: str | None = None) -> str:
        """Render a minimalist, readable HTML Telegram message for a NatalChart."""
        time_display = chart.birth_time_str or "не указано (12:00 UTC)"
        place_display = chart.birth_place or "не указано"
        lines: list[str] = [
            f"✨ <b>Натальная карта — {chart.subject_name}</b>",
            f"📅 {chart.birth_date.strftime('%d.%m.%Y')} | 🕒 {time_display}",
            f"📍 {place_display}",
            "",
            "<b>Положения планет (Swiss Ephemeris):</b>",
        ]

        for planet in chart.planets:
            retro = " ℞" if planet.is_retrograde else ""
            house_str = f" · {planet.house} дом" if planet.house is not None else ""
            lines.append(
                f"{planet.symbol} {planet.name_ru}: {planet.sign_symbol} {planet.sign_ru} "
                f"{_format_deg_min(planet.degree_in_sign)}{retro}{house_str}"
            )

        if chart.ascendant is not None and chart.midheaven is not None:
            lines.extend(
                [
                    "",
                    "<b>Углы карты и ключевые дома:</b>",
                    f"⬆️ Асцендент (I дом): {chart.ascendant.sign_symbol} {chart.ascendant.sign_ru} "
                    f"{_format_deg_min(chart.ascendant.degree_in_sign)}",
                    f"🏔 Середина Неба (X дом): {chart.midheaven.sign_symbol} {chart.midheaven.sign_ru} "
                    f"{_format_deg_min(chart.midheaven.degree_in_sign)}",
                ]
            )
            if chart.houses:
                cusp_summary = ", ".join(
                    f"{h.number}:{h.sign_symbol}{int(h.degree_in_sign)}°" for h in chart.houses
                )
                lines.append(f"🏛 Дома: {cusp_summary}")

        if chart.aspects:
            lines.append("")
            lines.append("<b>Ключевые аспекты (самые точные):</b>")
            for asp in chart.aspects[:6]:
                marker = "✦" if asp.is_harmonious else "⚡"
                lines.append(
                    f"{marker} {asp.body_a} — {asp.aspect_ru} — {asp.body_b} (орб {asp.orb:.1f}°)"
                )

        text_interp = interpretation or self.build_local_interpretation(chart)
        lines.extend(["", "<b>Разбор карты:</b>", text_interp])

        if chart.limitations:
            lines.append("")
            lines.append("⚠️ <b>Ограничения расчёта:</b>")
            for lim in chart.limitations:
                lines.append(f"• {lim}")

        return "\n".join(lines)
