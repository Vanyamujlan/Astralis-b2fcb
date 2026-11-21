"""Tests for 78-card Tarot deck, duplicate-free sampling, orientations, and history persistence."""

from __future__ import annotations

import pytest

from astralio.models.tarot import TarotSpreadType
from astralio.repositories.reading_repository import ReadingRepository
from astralio.services.tarot_deck import FULL_TAROT_DECK
from astralio.services.tarot_service import SPREAD_SPECS, TarotService
from tests.conftest import FakeFirestoreClient


def test_full_deck_has_78_unique_cards() -> None:
    assert len(FULL_TAROT_DECK) == 78
    ids = [card.card_id for card in FULL_TAROT_DECK]
    assert len(set(ids)) == 78
    assert sum(1 for c in FULL_TAROT_DECK if c.arcana == "major") == 22
    assert sum(1 for c in FULL_TAROT_DECK if c.arcana == "minor") == 56


def test_draw_cards_never_repeats_within_spread() -> None:
    repo = ReadingRepository(FakeFirestoreClient())
    service = TarotService(repo)

    for spread_type, spec in SPREAD_SPECS.items():
        for _ in range(30):
            drawn = service.draw_cards(spread_type)
            assert len(drawn) == len(spec.positions)
            card_ids = [c.card_id for c in drawn]
            assert len(set(card_ids)) == len(card_ids)


def test_draw_supports_both_upright_and_reversed_orientations() -> None:
    repo = ReadingRepository(FakeFirestoreClient())
    upright_service = TarotService(repo, reversed_probability=0.0)
    reversed_service = TarotService(repo, reversed_probability=1.0)

    up_cards = upright_service.draw_cards(TarotSpreadType.THREE_CARDS)
    rev_cards = reversed_service.draw_cards(TarotSpreadType.THREE_CARDS)

    assert all(not c.is_reversed for c in up_cards)
    assert all(c.is_reversed for c in rev_cards)

    # Verify upright and reversed meanings differ for the same card
    card = FULL_TAROT_DECK[0]
    assert card.upright_meaning != card.reversed_meaning
    assert card.upright_keywords != card.reversed_keywords


@pytest.mark.asyncio
async def test_tarot_reading_is_saved_and_loaded_from_history() -> None:
    repo = ReadingRepository(FakeFirestoreClient())
    service = TarotService(repo)

    r1 = await service.create_and_save_reading(
        telegram_id=777,
        spread_type=TarotSpreadType.ONE_CARD,
        question="На чём сфокусироваться сегодня?",
    )
    r2 = await service.create_and_save_reading(
        telegram_id=777,
        spread_type=TarotSpreadType.PATH_CHOICE,
        question=None,
    )

    assert len(r1.cards) == 1
    assert len(r2.cards) == 5

    history = await service.get_history(777, limit=5)
    assert len(history) == 2
    assert {item.reading_id for item in history} == {r1.reading_id, r2.reading_id}

    formatted = service.format_reading(r1)
    assert "Карта дня" in formatted
    assert "На чём сфокусироваться сегодня?" in formatted

    history_text = service.format_history(history)
    assert "Последние расклады Таро" in history_text
