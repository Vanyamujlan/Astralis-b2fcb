"""Tarot spread drawing service without duplicates, upright/reversed orientation, and history."""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from astralio.models.tarot import DrawnCard, TarotReading, TarotSpreadType
from astralio.repositories.reading_repository import ReadingRepository
from astralio.services.tarot_deck import FULL_TAROT_DECK


@dataclass(frozen=True, slots=True)
class SpreadSpec:
    """Definition of a Tarot spread."""

    spread_type: TarotSpreadType
    title: str
    description: str
    positions: tuple[str, ...]


SPREAD_SPECS: dict[TarotSpreadType, SpreadSpec] = {
    TarotSpreadType.ONE_CARD: SpreadSpec(
        spread_type=TarotSpreadType.ONE_CARD,
        title="Карта дня",
        description="1 карта — главный акцент дня и практический совет.",
        positions=("Главный фокус",),
    ),
    TarotSpreadType.THREE_CARDS: SpreadSpec(
        spread_type=TarotSpreadType.THREE_CARDS,
        title="Прошлое · Настоящее · Будущее",
        description="3 карты — развитие ситуации во времени.",
        positions=("Прошлое (истоки)", "Настоящее (суть момента)", "Ближайший вектор"),
    ),
    TarotSpreadType.RELATIONSHIP: SpreadSpec(
        spread_type=TarotSpreadType.RELATIONSHIP,
        title="Отношения",
        description="3 карты — ваша позиция, позиция партнёра и динамика союза.",
        positions=("Ваша позиция", "Позиция партнёра", "Динамика и совет"),
    ),
    TarotSpreadType.PATH_CHOICE: SpreadSpec(
        spread_type=TarotSpreadType.PATH_CHOICE,
        title="Выбор пути",
        description="5 карт — глубокий разбор решения и последствий.",
        positions=(
            "Суть вопроса",
            "Что помогает",
            "Что мешает",
            "Вероятный итог",
            "Ключевой совет",
        ),
    ),
}


class TarotService:
    """Draws fair Tarot readings without card repetition and persists reading history."""

    def __init__(
        self,
        reading_repository: ReadingRepository,
        *,
        reversed_probability: float = 0.30,
        rng: secrets.SystemRandom | None = None,
    ) -> None:
        self._reading_repo = reading_repository
        self._reversed_probability = reversed_probability
        self._rng = rng or secrets.SystemRandom()

    def list_spreads(self) -> list[SpreadSpec]:
        """Return all available Tarot spreads."""
        return list(SPREAD_SPECS.values())

    def get_spread_spec(self, spread_type: TarotSpreadType) -> SpreadSpec:
        return SPREAD_SPECS[spread_type]

    def draw_cards(self, spread_type: TarotSpreadType) -> list[DrawnCard]:
        """Draw unique cards without replacement for the requested spread."""
        spec = SPREAD_SPECS[spread_type]
        count = len(spec.positions)
        if count > len(FULL_TAROT_DECK):
            raise ValueError("Requested spread size exceeds Tarot deck size.")

        selected_cards = self._rng.sample(FULL_TAROT_DECK, k=count)
        drawn: list[DrawnCard] = []
        for idx, (position_title, card) in enumerate(
            zip(spec.positions, selected_cards, strict=True)
        ):
            is_reversed = self._rng.random() < self._reversed_probability
            drawn.append(
                DrawnCard(
                    position_index=idx,
                    position_title=position_title,
                    card_id=card.card_id,
                    name_ru=card.name_ru,
                    is_reversed=is_reversed,
                    keywords=card.reversed_keywords if is_reversed else card.upright_keywords,
                    meaning=card.reversed_meaning if is_reversed else card.upright_meaning,
                    advice=card.advice,
                )
            )
        return drawn

    def build_local_summary(self, cards: list[DrawnCard], question: str | None = None) -> str:
        """Synthesize a concise, grounded local summary from drawn cards."""
        reversed_count = sum(1 for c in cards if c.is_reversed)
        major_count = sum(1 for c in cards if c.card_id.startswith("major_"))

        parts: list[str] = []
        if question:
            parts.append(f"По запросу «{question}» расклад выделяет следующие ориентиры.")

        if major_count >= max(2, len(cards) // 2 + 1):
            parts.append(
                "В раскладе много Старших Арканов — ситуация затрагивает значимый жизненный этап и ключевые решения."
            )
        elif reversed_count > len(cards) // 2:
            parts.append(
                "Преобладают перевёрнутые карты: энергия ситуации сейчас направлена внутрь, "
                "важно убрать спешку и устранить скрытые задержки."
            )
        else:
            parts.append(
                "Расклад показывает открытый и понятный вектор — практические шаги дадут заметный отклик."
            )

        closing = cards[-1]
        parts.append(f"Итоговый ориентир ({closing.name_ru}): {closing.advice}")
        return " ".join(parts)

    async def create_and_save_reading(
        self,
        *,
        telegram_id: int,
        spread_type: TarotSpreadType,
        question: str | None = None,
        summary_override: str | None = None,
        interpretation_source: str = "local",
    ) -> TarotReading:
        """Draw cards, compose summary, and save reading to Firestore."""
        spec = SPREAD_SPECS[spread_type]
        drawn = self.draw_cards(spread_type)
        summary = summary_override or self.build_local_summary(drawn, question=question)
        reading = TarotReading(
            reading_id=uuid.uuid4().hex[:16],
            telegram_id=telegram_id,
            spread_type=spread_type,
            spread_title=spec.title,
            question=question.strip() if question and question.strip() else None,
            cards=drawn,
            summary=summary,
            interpretation_source=interpretation_source,
            created_at=datetime.now(UTC),
        )
        await self._reading_repo.save_tarot_reading(reading)
        return reading

    async def get_history(self, telegram_id: int, *, limit: int = 5) -> list[TarotReading]:
        """Retrieve user's saved Tarot readings."""
        return await self._reading_repo.list_tarot_readings(telegram_id, limit=limit)

    def format_reading(self, reading: TarotReading) -> str:
        """Render a TarotReading as clean Telegram HTML."""
        lines = [f"🃏 <b>Таро — {reading.spread_title}</b>"]
        if reading.question:
            lines.append(f"❓ Вопрос: <i>{reading.question}</i>")
        lines.append("")

        for card in reading.cards:
            orient = "перевёрнутая" if card.is_reversed else "прямая"
            orient_icon = "🔄" if card.is_reversed else "⬆️"
            lines.append(
                f"<b>{card.position_index + 1}. {card.position_title}:</b> "
                f"{card.name_ru} ({orient_icon} {orient})"
            )
            lines.append(f"<i>Ключевые слова:</i> {card.keywords}")
            lines.append(card.meaning)
            lines.append("")

        lines.extend(["<b>Общий итог:</b>", reading.summary])
        return "\n".join(lines)

    def format_history(self, readings: list[TarotReading]) -> str:
        """Render recent saved Tarot readings as a compact list."""
        if not readings:
            return (
                "📚 <b>История раскладов Таро</b>\n\n"
                "У вас пока нет сохранённых раскладов. Выберите расклад в меню Таро, "
                "и результат автоматически сохранится здесь."
            )

        lines = ["📚 <b>Последние расклады Таро</b>", ""]
        for idx, item in enumerate(readings, start=1):
            date_str = item.created_at.strftime("%d.%m.%Y %H:%M UTC")
            cards_str = ", ".join(
                f"{c.name_ru}{' (перев.)' if c.is_reversed else ''}" for c in item.cards
            )
            q_part = f"\n   Вопрос: <i>{item.question}</i>" if item.question else ""
            lines.append(
                f"<b>{idx}. {item.spread_title}</b> · {date_str}{q_part}\n   Карты: {cards_str}"
            )
        return "\n".join(lines)
