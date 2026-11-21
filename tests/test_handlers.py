"""End-to-end Telegram handler & conversation flow tests driven through PTB Application."""

from __future__ import annotations

from typing import Any

import pytest

from astralio.app import build_application
from astralio.config import Settings
from astralio.keyboards.callbacks import CB
from tests.conftest import (
    FakeFirestoreClient,
    MockBotRecorder,
    attach_mock_bot,
    make_callback_update,
    make_pre_checkout_update,
    make_successful_payment_update,
    make_text_update,
)


@pytest.mark.asyncio
async def test_start_registers_user_and_displays_all_seven_buttons(
    wired_app: tuple[Any, MockBotRecorder],
    fake_db: FakeFirestoreClient,
) -> None:
    app, recorder = wired_app
    await app.process_update(make_text_update(app.bot, "/start", user_id=2001, first_name="Елена"))

    assert "users/2001" in fake_db.store
    assert len(recorder.sent_messages) == 1
    msg = recorder.sent_messages[-1]
    assert "Astralio" in msg["text"]
    markup = msg["reply_markup"]
    button_labels = [btn.text for row in markup.inline_keyboard for btn in row]
    assert any("Натальная карта" in lbl for lbl in button_labels)
    assert any("Совместимость" in lbl for lbl in button_labels)
    assert any("Прогнозы" in lbl for lbl in button_labels)
    assert any("Таро" in lbl for lbl in button_labels)
    assert any("Профиль" in lbl for lbl in button_labels)
    assert any("Premium" in lbl for lbl in button_labels)
    assert any("Помощь" in lbl for lbl in button_labels)


@pytest.mark.asyncio
async def test_profile_view_and_edit_birth_fields_with_validation(
    wired_app: tuple[Any, MockBotRecorder],
    fake_db: FakeFirestoreClient,
) -> None:
    app, recorder = wired_app
    uid = 2002

    # Open profile
    await app.process_update(
        make_callback_update(app.bot, CB.MENU_PROFILE, user_id=uid, update_id=1)
    )
    assert "Профиль Astralio" in recorder.last_text

    # Edit date: invalid input then valid input
    await app.process_update(
        make_callback_update(app.bot, CB.PROFILE_EDIT_DATE, user_id=uid, update_id=2)
    )
    await app.process_update(make_text_update(app.bot, "99.99.9999", user_id=uid, update_id=3))
    assert "⚠️" in recorder.last_text

    await app.process_update(make_text_update(app.bot, "15.05.1995", user_id=uid, update_id=4))
    assert "15.05.1995" in recorder.last_text
    assert fake_db.store[f"users/{uid}"]["birth_data"]["birth_date"] == "1995-05-15"

    # Edit time -> unknown button
    await app.process_update(
        make_callback_update(app.bot, CB.PROFILE_EDIT_TIME, user_id=uid, update_id=5)
    )
    await app.process_update(
        make_callback_update(app.bot, CB.PROFILE_TIME_UNKNOWN, user_id=uid, update_id=6)
    )
    assert fake_db.store[f"users/{uid}"]["birth_data"]["birth_time_unknown"] is True

    # Edit place -> valid city
    await app.process_update(
        make_callback_update(app.bot, CB.PROFILE_EDIT_PLACE, user_id=uid, update_id=7)
    )
    await app.process_update(make_text_update(app.bot, "Москва", user_id=uid, update_id=8))
    assert "Москва" in recorder.last_text
    assert fake_db.store[f"users/{uid}"]["birth_data"]["timezone"] == "Europe/Moscow"


@pytest.mark.asyncio
async def test_natal_chart_wizard_full_flow_back_and_from_profile(
    wired_app: tuple[Any, MockBotRecorder],
) -> None:
    app, recorder = wired_app
    uid = 2003

    await app.process_update(make_callback_update(app.bot, CB.MENU_NATAL, user_id=uid, update_id=1))
    assert "Натальная карта" in recorder.last_text

    # Start wizard -> Date -> Time -> Back to Date -> Date -> Time -> Place -> Result
    await app.process_update(make_callback_update(app.bot, CB.NATAL_NEW, user_id=uid, update_id=2))
    await app.process_update(make_text_update(app.bot, "15.05.1995", user_id=uid, update_id=3))
    assert "шаг 2 из 3" in recorder.last_text

    # Back to step 1
    await app.process_update(make_callback_update(app.bot, CB.NAV_BACK, user_id=uid, update_id=4))
    assert "шаг 1 из 3" in recorder.last_text

    await app.process_update(make_text_update(app.bot, "15.05.1995", user_id=uid, update_id=5))
    await app.process_update(make_text_update(app.bot, "14:30", user_id=uid, update_id=6))
    assert "шаг 3 из 3" in recorder.last_text

    await app.process_update(make_text_update(app.bot, "Москва", user_id=uid, update_id=7))
    assert "Swiss Ephemeris" in recorder.last_text
    assert "Телец" in recorder.last_text
    assert "Асцендент" in recorder.last_text

    # Instant calculation from saved profile now works
    await app.process_update(
        make_callback_update(app.bot, CB.NATAL_FROM_PROFILE, user_id=uid, update_id=8)
    )
    assert "Натальная карта" in recorder.last_text
    assert "Телец" in recorder.last_text


@pytest.mark.asyncio
async def test_natal_wizard_unknown_time_shows_limitations(
    wired_app: tuple[Any, MockBotRecorder],
) -> None:
    app, recorder = wired_app
    uid = 2004

    await app.process_update(make_callback_update(app.bot, CB.NATAL_NEW, user_id=uid, update_id=1))
    await app.process_update(make_text_update(app.bot, "10.01.1990", user_id=uid, update_id=2))
    await app.process_update(
        make_callback_update(app.bot, CB.NATAL_TIME_UNKNOWN, user_id=uid, update_id=3)
    )
    await app.process_update(
        make_callback_update(app.bot, CB.NATAL_PLACE_SKIP, user_id=uid, update_id=4)
    )
    assert "Ограничения расчёта" in recorder.last_text
    assert "Козерог" in recorder.last_text


@pytest.mark.asyncio
async def test_compatibility_manual_wizard_and_cancel(
    wired_app: tuple[Any, MockBotRecorder],
) -> None:
    app, recorder = wired_app
    uid = 2005

    await app.process_update(
        make_callback_update(app.bot, CB.MENU_COMPAT, user_id=uid, update_id=1)
    )
    await app.process_update(
        make_callback_update(app.bot, CB.COMPAT_MANUAL, user_id=uid, update_id=2)
    )
    await app.process_update(make_text_update(app.bot, "Анна", user_id=uid, update_id=3))
    await app.process_update(make_text_update(app.bot, "15.05.1995", user_id=uid, update_id=4))
    await app.process_update(make_text_update(app.bot, "14:30", user_id=uid, update_id=5))
    await app.process_update(make_text_update(app.bot, "Москва", user_id=uid, update_id=6))
    await app.process_update(make_text_update(app.bot, "Дмитрий", user_id=uid, update_id=7))
    await app.process_update(make_text_update(app.bot, "18.09.1994", user_id=uid, update_id=8))
    await app.process_update(
        make_callback_update(app.bot, CB.COMPAT_TIME_UNKNOWN, user_id=uid, update_id=9)
    )
    await app.process_update(
        make_callback_update(app.bot, CB.COMPAT_PLACE_SKIP, user_id=uid, update_id=10)
    )

    assert "Совместимость: Анна и Дмитрий" in recorder.last_text
    assert "Общая совместимость:" in recorder.last_text

    # Test cancel mid-wizard
    await app.process_update(
        make_callback_update(app.bot, CB.COMPAT_MANUAL, user_id=uid, update_id=11)
    )
    await app.process_update(
        make_callback_update(app.bot, CB.NAV_CANCEL, user_id=uid, update_id=12)
    )
    assert "Операция отменена" in recorder.last_text


@pytest.mark.asyncio
async def test_forecasts_require_birth_data_then_compute_daily_and_weekly(
    wired_app: tuple[Any, MockBotRecorder],
) -> None:
    app, recorder = wired_app
    uid = 2006

    # Without birth data -> honest prompt (never fake forecast)
    await app.process_update(
        make_callback_update(app.bot, CB.MENU_FORECAST, user_id=uid, update_id=1)
    )
    await app.process_update(
        make_callback_update(app.bot, CB.FORECAST_DAILY, user_id=uid, update_id=2)
    )
    assert "Недостаточно данных" in recorder.last_text

    # Fill birth date via profile edit
    await app.process_update(
        make_callback_update(app.bot, CB.PROFILE_EDIT_DATE, user_id=uid, update_id=3)
    )
    await app.process_update(make_text_update(app.bot, "15.05.1995", user_id=uid, update_id=4))

    # Daily & Weekly forecasts now compute real transits
    await app.process_update(
        make_callback_update(app.bot, CB.FORECAST_DAILY, user_id=uid, update_id=5)
    )
    assert "Персональный прогноз на" in recorder.last_text
    assert "Телец" in recorder.last_text

    await app.process_update(
        make_callback_update(app.bot, CB.FORECAST_WEEKLY, user_id=uid, update_id=6)
    )
    assert "Персональный прогноз на неделю" in recorder.last_text


@pytest.mark.asyncio
async def test_tarot_draw_with_question_skip_and_history(
    wired_app: tuple[Any, MockBotRecorder],
) -> None:
    app, recorder = wired_app
    uid = 2007

    await app.process_update(make_callback_update(app.bot, CB.MENU_TAROT, user_id=uid, update_id=1))
    assert "Таро Astralio" in recorder.last_text

    # Spread with question
    await app.process_update(
        make_callback_update(app.bot, CB.TAROT_SPREAD_THREE, user_id=uid, update_id=2)
    )
    await app.process_update(
        make_text_update(app.bot, "Как сложится проект?", user_id=uid, update_id=3)
    )
    assert "Прошлое · Настоящее · Будущее" in recorder.last_text
    assert "Как сложится проект?" in recorder.last_text

    # Spread without question
    await app.process_update(
        make_callback_update(app.bot, CB.TAROT_SPREAD_ONE, user_id=uid, update_id=4)
    )
    await app.process_update(
        make_callback_update(app.bot, CB.TAROT_SKIP_QUESTION, user_id=uid, update_id=5)
    )
    assert "Карта дня" in recorder.last_text

    # History displays both readings
    await app.process_update(
        make_callback_update(app.bot, CB.TAROT_HISTORY, user_id=uid, update_id=6)
    )
    assert "Последние расклады Таро" in recorder.last_text
    assert "Карта дня" in recorder.last_text


@pytest.mark.asyncio
async def test_premium_never_fakes_activation_and_supports_real_stars_flow(
    fake_db: FakeFirestoreClient,
    test_settings: Settings,
) -> None:
    # 1. With TELEGRAM_STARS_ENABLED=False, clicking a plan must NOT activate Premium
    app_disabled = build_application(test_settings, firestore_client=fake_db)
    rec_disabled = attach_mock_bot(app_disabled)
    uid = 2008

    await app_disabled.process_update(
        make_callback_update(app_disabled.bot, CB.MENU_PREMIUM, user_id=uid, update_id=1)
    )
    assert "Astralio Premium" in rec_disabled.last_text

    await app_disabled.process_update(
        make_callback_update(app_disabled.bot, CB.PREMIUM_BUY_MONTHLY, user_id=uid, update_id=2)
    )
    assert "не имитируем оплату" in rec_disabled.last_text
    assert fake_db.store[f"users/{uid}"]["subscription"]["is_active"] is False

    await app_disabled.process_update(
        make_callback_update(app_disabled.bot, CB.PREMIUM_STATUS, user_id=uid, update_id=3)
    )
    assert "Базовый (бесплатный)" in rec_disabled.last_text

    # 2. With TELEGRAM_STARS_ENABLED=True, real invoice + pre_checkout + successful_payment activates idempotently
    stars_settings = test_settings.model_copy(update={"telegram_stars_enabled": True})
    app_enabled = build_application(stars_settings, firestore_client=fake_db)
    rec_enabled = attach_mock_bot(app_enabled)

    await app_enabled.process_update(
        make_callback_update(app_enabled.bot, CB.PREMIUM_BUY_MONTHLY, user_id=uid, update_id=4)
    )
    assert len(rec_enabled.sent_invoices) == 1
    invoice_payload = rec_enabled.sent_invoices[0]["payload"]

    await app_enabled.process_update(
        make_pre_checkout_update(app_enabled.bot, payload=invoice_payload, user_id=uid, update_id=5)
    )
    assert rec_enabled.pre_checkout_answers[-1]["ok"] is True

    await app_enabled.process_update(
        make_successful_payment_update(
            app_enabled.bot,
            payload=invoice_payload,
            charge_id="stars_charge_xyz",
            user_id=uid,
            update_id=6,
        )
    )
    assert "Оплата Telegram Stars подтверждена" in rec_enabled.last_text
    assert fake_db.store[f"users/{uid}"]["subscription"]["is_active"] is True

    # Replay same payment update -> ignored safely
    await app_enabled.process_update(
        make_successful_payment_update(
            app_enabled.bot,
            payload=invoice_payload,
            charge_id="stars_charge_xyz",
            user_id=uid,
            update_id=7,
        )
    )
    assert "уже был обработан ранее" in rec_enabled.last_text


@pytest.mark.asyncio
async def test_help_guide_feedback_unknown_command_and_invalid_callback(
    wired_app: tuple[Any, MockBotRecorder],
    fake_db: FakeFirestoreClient,
) -> None:
    app, recorder = wired_app
    uid = 2009

    # Help menu & guide
    await app.process_update(make_callback_update(app.bot, CB.MENU_HELP, user_id=uid, update_id=1))
    await app.process_update(make_callback_update(app.bot, CB.HELP_GUIDE, user_id=uid, update_id=2))
    assert "Инструкция по функциям" in recorder.last_text

    # Feedback validation & persistence
    await app.process_update(
        make_callback_update(app.bot, CB.HELP_FEEDBACK, user_id=uid, update_id=3)
    )
    await app.process_update(make_text_update(app.bot, "ок", user_id=uid, update_id=4))
    assert "слишком короткое" in recorder.last_text

    await app.process_update(
        make_text_update(app.bot, "Спасибо за точные расчёты и Таро!", user_id=uid, update_id=5)
    )
    assert "Спасибо за обратную связь" in recorder.last_text
    assert any(k.startswith("feedback/") for k in fake_db.store)

    # Unknown slash command
    await app.process_update(make_text_update(app.bot, "/doesnotexist", user_id=uid, update_id=6))
    assert "Неизвестная команда" in recorder.last_text

    # Malformed / spoofed callback_data
    await app.process_update(
        make_callback_update(app.bot, "malicious:payload:drop_table", user_id=uid, update_id=7)
    )
    assert "Некорректное или устаревшее действие" in recorder.last_text
