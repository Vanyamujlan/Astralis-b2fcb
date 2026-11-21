"""Geographic place resolution with built-in city gazetteer and optional Nominatim fallback."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from timezonefinder import TimezoneFinder

from astralio.models.astrology import GeoLocation

logger = logging.getLogger(__name__)

_COORDS_RE = re.compile(r"^\s*(-?\d{1,2}(?:\.\d+)?)\s*[,;\s]\s*(-?\d{1,3}(?:\.\d+)?)\s*$")

# Built-in verified coordinates and IANA timezones for major Russian, CIS, and world cities.
# Format: normalized_alias -> (display_name, latitude, longitude, iana_timezone)
_BUILTIN_CITIES: dict[str, tuple[str, float, float, str]] = {
    "москва": ("Москва, Россия", 55.7558, 37.6173, "Europe/Moscow"),
    "moscow": ("Москва, Россия", 55.7558, 37.6173, "Europe/Moscow"),
    "санкт-петербург": ("Санкт-Петербург, Россия", 59.9343, 30.3351, "Europe/Moscow"),
    "санкт петербург": ("Санкт-Петербург, Россия", 59.9343, 30.3351, "Europe/Moscow"),
    "спб": ("Санкт-Петербург, Россия", 59.9343, 30.3351, "Europe/Moscow"),
    "питер": ("Санкт-Петербург, Россия", 59.9343, 30.3351, "Europe/Moscow"),
    "saint petersburg": ("Санкт-Петербург, Россия", 59.9343, 30.3351, "Europe/Moscow"),
    "st petersburg": ("Санкт-Петербург, Россия", 59.9343, 30.3351, "Europe/Moscow"),
    "новосибирск": ("Новосибирск, Россия", 55.0084, 82.9357, "Asia/Novosibirsk"),
    "novosibirsk": ("Новосибирск, Россия", 55.0084, 82.9357, "Asia/Novosibirsk"),
    "екатеринбург": ("Екатеринбург, Россия", 56.8389, 60.6057, "Asia/Yekaterinburg"),
    "екб": ("Екатеринбург, Россия", 56.8389, 60.6057, "Asia/Yekaterinburg"),
    "yekaterinburg": ("Екатеринбург, Россия", 56.8389, 60.6057, "Asia/Yekaterinburg"),
    "казань": ("Казань, Россия", 55.7961, 49.1064, "Europe/Moscow"),
    "kazan": ("Казань, Россия", 55.7961, 49.1064, "Europe/Moscow"),
    "нижний новгород": ("Нижний Новгород, Россия", 56.3269, 44.0059, "Europe/Moscow"),
    "челябинск": ("Челябинск, Россия", 55.1644, 61.4368, "Asia/Yekaterinburg"),
    "самара": ("Самара, Россия", 53.1959, 50.1002, "Europe/Samara"),
    "омск": ("Омск, Россия", 54.9885, 73.3242, "Asia/Omsk"),
    "ростов-на-дону": ("Ростов-на-Дону, Россия", 47.2357, 39.7015, "Europe/Moscow"),
    "ростов на дону": ("Ростов-на-Дону, Россия", 47.2357, 39.7015, "Europe/Moscow"),
    "уфа": ("Уфа, Россия", 54.7388, 55.9721, "Asia/Yekaterinburg"),
    "красноярск": ("Красноярск, Россия", 56.0153, 92.8932, "Asia/Krasnoyarsk"),
    "воронеж": ("Воронеж, Россия", 51.6755, 39.2089, "Europe/Moscow"),
    "пермь": ("Пермь, Россия", 58.0105, 56.2502, "Asia/Yekaterinburg"),
    "волгоград": ("Волгоград, Россия", 48.7080, 44.5133, "Europe/Volgograd"),
    "краснодар": ("Краснодар, Россия", 45.0355, 38.9753, "Europe/Moscow"),
    "сочи": ("Сочи, Россия", 43.5855, 39.7231, "Europe/Moscow"),
    "саратов": ("Саратов, Россия", 51.5336, 46.0343, "Europe/Saratov"),
    "тюмень": ("Тюмень, Россия", 57.1522, 65.5272, "Asia/Yekaterinburg"),
    "иркутск": ("Иркутск, Россия", 52.2869, 104.3050, "Asia/Irkutsk"),
    "хабаровск": ("Хабаровск, Россия", 48.4802, 135.0719, "Asia/Vladivostok"),
    "владивосток": ("Владивосток, Россия", 43.1155, 131.8855, "Asia/Vladivostok"),
    "калининград": ("Калининград, Россия", 54.7104, 20.4522, "Europe/Kaliningrad"),
    "мурманск": ("Мурманск, Россия", 68.9585, 33.0827, "Europe/Moscow"),
    "ярославль": ("Ярославль, Россия", 57.6261, 39.8845, "Europe/Moscow"),
    "томск": ("Томск, Россия", 56.4846, 84.9476, "Asia/Tomsk"),
    "барнаул": ("Барнаул, Россия", 53.3548, 83.7698, "Asia/Barnaul"),
    "махачкала": ("Махачкала, Россия", 42.9849, 47.5047, "Europe/Moscow"),
    "минск": ("Минск, Беларусь", 53.9006, 27.5590, "Europe/Minsk"),
    "minsk": ("Минск, Беларусь", 53.9006, 27.5590, "Europe/Minsk"),
    "киев": ("Киев, Украина", 50.4501, 30.5234, "Europe/Kyiv"),
    "kyiv": ("Киев, Украина", 50.4501, 30.5234, "Europe/Kyiv"),
    "kiev": ("Киев, Украина", 50.4501, 30.5234, "Europe/Kyiv"),
    "одесса": ("Одесса, Украина", 46.4825, 30.7233, "Europe/Kyiv"),
    "львов": ("Львов, Украина", 49.8397, 24.0297, "Europe/Kyiv"),
    "алматы": ("Алматы, Казахстан", 43.2389, 76.8897, "Asia/Almaty"),
    "almaty": ("Алматы, Казахстан", 43.2389, 76.8897, "Asia/Almaty"),
    "астана": ("Астана, Казахстан", 51.1694, 71.4491, "Asia/Almaty"),
    "astana": ("Астана, Казахстан", 51.1694, 71.4491, "Asia/Almaty"),
    "ташкент": ("Ташкент, Узбекистан", 41.2995, 69.2401, "Asia/Tashkent"),
    "tashkent": ("Ташкент, Узбекистан", 41.2995, 69.2401, "Asia/Tashkent"),
    "бишкек": ("Бишкек, Кыргызстан", 42.8746, 74.5698, "Asia/Bishkek"),
    "тбилиси": ("Тбилиси, Грузия", 41.7151, 44.8271, "Asia/Tbilisi"),
    "tbilisi": ("Тбилиси, Грузия", 41.7151, 44.8271, "Asia/Tbilisi"),
    "батуми": ("Батуми, Грузия", 41.6168, 41.6367, "Asia/Tbilisi"),
    "ереван": ("Ереван, Армения", 40.1792, 44.4991, "Asia/Yerevan"),
    "yerevan": ("Ереван, Армения", 40.1792, 44.4991, "Asia/Yerevan"),
    "баку": ("Баку, Азербайджан", 40.4093, 49.8671, "Asia/Baku"),
    "baku": ("Баку, Азербайджан", 40.4093, 49.8671, "Asia/Baku"),
    "кишинёв": ("Кишинёв, Молдова", 47.0105, 28.8638, "Europe/Chisinau"),
    "кишинев": ("Кишинёв, Молдова", 47.0105, 28.8638, "Europe/Chisinau"),
    "рига": ("Рига, Латвия", 56.9496, 24.1052, "Europe/Riga"),
    "вильнюс": ("Вильнюс, Литва", 54.6872, 25.2797, "Europe/Vilnius"),
    "таллин": ("Таллин, Эстония", 59.4370, 24.7536, "Europe/Tallinn"),
    "лондон": ("Лондон, Великобритания", 51.5072, -0.1276, "Europe/London"),
    "london": ("Лондон, Великобритания", 51.5072, -0.1276, "Europe/London"),
    "париж": ("Париж, Франция", 48.8566, 2.3522, "Europe/Paris"),
    "paris": ("Париж, Франция", 48.8566, 2.3522, "Europe/Paris"),
    "берлин": ("Берлин, Германия", 52.5200, 13.4050, "Europe/Berlin"),
    "berlin": ("Берлин, Германия", 52.5200, 13.4050, "Europe/Berlin"),
    "прага": ("Прага, Чехия", 50.0755, 14.4378, "Europe/Prague"),
    "prague": ("Прага, Чехия", 50.0755, 14.4378, "Europe/Prague"),
    "варшава": ("Варшава, Польша", 52.2297, 21.0122, "Europe/Warsaw"),
    "warsaw": ("Варшава, Польша", 52.2297, 21.0122, "Europe/Warsaw"),
    "вена": ("Вена, Австрия", 48.2082, 16.3738, "Europe/Vienna"),
    "рим": ("Рим, Италия", 41.9028, 12.4964, "Europe/Rome"),
    "rome": ("Рим, Италия", 41.9028, 12.4964, "Europe/Rome"),
    "мадрид": ("Мадрид, Испания", 40.4168, -3.7038, "Europe/Madrid"),
    "барселона": ("Барселона, Испания", 41.3874, 2.1686, "Europe/Madrid"),
    "barcelona": ("Барселона, Испания", 41.3874, 2.1686, "Europe/Madrid"),
    "амстердам": ("Амстердам, Нидерланды", 52.3676, 4.9041, "Europe/Amsterdam"),
    "стамбул": ("Стамбул, Турция", 41.0082, 28.9784, "Europe/Istanbul"),
    "istanbul": ("Стамбул, Турция", 41.0082, 28.9784, "Europe/Istanbul"),
    "анталия": ("Анталия, Турция", 36.8969, 30.7133, "Europe/Istanbul"),
    "дубай": ("Дубай, ОАЭ", 25.2048, 55.2708, "Asia/Dubai"),
    "dubai": ("Дубай, ОАЭ", 25.2048, 55.2708, "Asia/Dubai"),
    "тель-авив": ("Тель-Авив, Израиль", 32.0853, 34.7818, "Asia/Jerusalem"),
    "нью-йорк": ("Нью-Йорк, США", 40.7128, -74.0060, "America/New_York"),
    "new york": ("Нью-Йорк, США", 40.7128, -74.0060, "America/New_York"),
    "лос-анджелес": ("Лос-Анджелес, США", 34.0522, -118.2437, "America/Los_Angeles"),
    "los angeles": ("Лос-Анджелес, США", 34.0522, -118.2437, "America/Los_Angeles"),
    "торонто": ("Торонто, Канада", 43.6532, -79.3832, "America/Toronto"),
    "токио": ("Токио, Япония", 35.6762, 139.6503, "Asia/Tokyo"),
    "tokyo": ("Токио, Япония", 35.6762, 139.6503, "Asia/Tokyo"),
    "сеул": ("Сеул, Южная Корея", 37.5665, 126.9780, "Asia/Seoul"),
    "бангкок": ("Бангкок, Таиланд", 13.7563, 100.5018, "Asia/Bangkok"),
    "сингапур": ("Сингапур", 1.3521, 103.8198, "Asia/Singapore"),
    "сидней": ("Сидней, Австралия", -33.8688, 151.2093, "Australia/Sydney"),
}


class GeocodingService:
    """Resolves city names or raw coordinates to GeoLocation (lat, lon, timezone)."""

    def __init__(
        self,
        *,
        remote_enabled: bool = True,
        timeout_seconds: float = 5.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._remote_enabled = remote_enabled
        self._timeout_seconds = timeout_seconds
        self._http_client = http_client
        self._tz_finder = TimezoneFinder()

    def _normalize_query(self, raw: str) -> str:
        cleaned = re.sub(r"\s+", " ", raw.strip().lower())
        cleaned = cleaned.replace("ё", "е")
        # If user typed "Москва, Россия", also check leading city segment
        return cleaned

    def _lookup_timezone(self, lat: float, lon: float) -> str:
        tz = self._tz_finder.timezone_at(lat=lat, lng=lon)
        return tz or "UTC"

    def resolve_local(self, query: str) -> GeoLocation | None:
        """Resolve direct coordinates or built-in gazetteer entry without network calls."""
        text = query.strip()
        if not text:
            return None

        # 1. Direct lat, lon input
        match = _COORDS_RE.match(text)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                tz = self._lookup_timezone(lat, lon)
                return GeoLocation(
                    name=f"{lat:.4f}, {lon:.4f}",
                    latitude=lat,
                    longitude=lon,
                    timezone=tz,
                    source="coordinates",
                )
            return None

        # 2. Built-in gazetteer lookup (exact or leading city before comma)
        normalized = self._normalize_query(text)
        candidates = [normalized]
        if "," in normalized:
            candidates.append(normalized.split(",", 1)[0].strip())

        for candidate in candidates:
            entry = _BUILTIN_CITIES.get(candidate)
            if entry is None and "е" in candidate:
                # Match entries that contain 'ё' in keys
                for key, val in _BUILTIN_CITIES.items():
                    if key.replace("ё", "е") == candidate:
                        entry = val
                        break
            if entry is not None:
                display_name, lat, lon, tz = entry
                return GeoLocation(
                    name=display_name,
                    latitude=lat,
                    longitude=lon,
                    timezone=tz,
                    source="gazetteer",
                )
        return None

    async def resolve(self, query: str) -> GeoLocation | None:
        """Resolve city name or coordinates via gazetteer first, then Nominatim if enabled."""
        local = self.resolve_local(query)
        if local is not None:
            return local

        if not self._remote_enabled:
            return None

        cleaned = query.strip()
        if len(cleaned) < 2:
            return None

        params = {
            "q": cleaned,
            "format": "json",
            "limit": "1",
            "accept-language": "ru",
        }
        headers = {"User-Agent": "AstralioTelegramBot/0.1 (astrology-mvp)"}

        try:
            if self._http_client is not None:
                response = await self._http_client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params=params,
                    headers=headers,
                    timeout=self._timeout_seconds,
                )
            else:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.get(
                        "https://nominatim.openstreetmap.org/search",
                        params=params,
                        headers=headers,
                    )
            response.raise_for_status()
            payload: list[dict[str, Any]] = response.json()
            if not payload:
                return None

            top = payload[0]
            lat = float(top["lat"])
            lon = float(top["lon"])
            raw_display = str(top.get("display_name") or cleaned)
            short_name = ", ".join(part.strip() for part in raw_display.split(",")[:2])
            tz = self._lookup_timezone(lat, lon)
            return GeoLocation(
                name=short_name or cleaned,
                latitude=lat,
                longitude=lon,
                timezone=tz,
                source="nominatim",
            )
        except Exception as exc:
            logger.warning("Remote geocoding failed for query=%r: %s", cleaned, type(exc).__name__)
            return None
