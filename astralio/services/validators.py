"""Strict validators and parsers for user-provided birth and profile inputs."""

from __future__ import annotations

import re
from datetime import date, time

_DATE_DOT_RE = re.compile(r"^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$")
_DATE_ISO_RE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_TIME_RE = re.compile(r"^(\d{1,2})[:.\s](\d{2})$")

_UNKNOWN_TIME_TOKENS = {
    "неизвестно",
    "не знаю",
    "незнаю",
    "нет",
    "пропустить",
    "unknown",
    "-",
    "?",
}


class InputValidationError(ValueError):
    """Raised when user input does not match expected format or bounds."""


def parse_birth_date(raw: str, *, today: date | None = None) -> date:
    """Parse birth date in DD.MM.YYYY (or YYYY-MM-DD) format with strict range checks."""
    text = raw.strip()
    if not text:
        raise InputValidationError(
            "Введите дату рождения в формате ДД.ММ.ГГГГ, например: 15.05.1995."
        )

    day: int
    month: int
    year: int

    dot_match = _DATE_DOT_RE.match(text)
    iso_match = _DATE_ISO_RE.match(text)
    if dot_match:
        day, month, year = int(dot_match.group(1)), int(dot_match.group(2)), int(dot_match.group(3))
    elif iso_match:
        year, month, day = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
    else:
        raise InputValidationError(
            "Неверный формат даты. Используйте ДД.ММ.ГГГГ, например: 15.05.1995."
        )

    try:
        parsed = date(year, month, day)
    except ValueError as exc:
        raise InputValidationError(
            "Такой календарной даты не существует. Проверьте день и месяц."
        ) from exc

    reference_today = today or date.today()
    if parsed < date(1900, 1, 1):
        raise InputValidationError("Укажите дату рождения начиная с 01.01.1900.")
    if parsed > reference_today:
        raise InputValidationError("Дата рождения не может быть в будущем.")
    return parsed


def parse_birth_time(raw: str) -> tuple[time | None, bool]:
    """Parse birth time in HH:MM format or explicit unknown marker.

    Returns `(parsed_time, is_unknown)`.
    """
    text = raw.strip().lower()
    if not text:
        raise InputValidationError(
            "Введите время рождения в формате ЧЧ:ММ (например, 14:30) или напишите «неизвестно»."
        )
    if text in _UNKNOWN_TIME_TOKENS:
        return None, True

    match = _TIME_RE.match(text)
    if not match:
        raise InputValidationError(
            "Неверный формат времени. Используйте ЧЧ:ММ (например, 09:45) или нажмите «Время неизвестно»."
        )
    hour = int(match.group(1))
    minute = int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise InputValidationError("Часы должны быть от 00 до 23, а минуты от 00 до 59.")
    return time(hour, minute), False


def parse_person_name(raw: str) -> str:
    """Validate and normalize a person's display name."""
    cleaned = re.sub(r"\s+", " ", raw.strip())
    if len(cleaned) < 2 or len(cleaned) > 60:
        raise InputValidationError("Имя должно содержать от 2 до 60 символов.")
    if cleaned.startswith("/"):
        raise InputValidationError("Введите имя текстом, а не команду.")
    return cleaned


def validate_feedback_text(raw: str) -> str:
    """Validate feedback message content."""
    cleaned = raw.strip()
    if len(cleaned) < 5:
        raise InputValidationError("Сообщение слишком короткое — напишите хотя бы 5 символов.")
    if len(cleaned) > 2000:
        raise InputValidationError("Сообщение слишком длинное (максимум 2000 символов).")
    return cleaned
