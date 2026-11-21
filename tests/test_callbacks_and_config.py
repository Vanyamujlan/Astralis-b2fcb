"""Integrity checks for callback_data coverage, secret redaction, and configuration."""

from __future__ import annotations

import logging
import re

import pytest
from pydantic import ValidationError
from telegram import InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, ConversationHandler

from astralio.app import build_application
from astralio.config import Settings
from astralio.infrastructure.logging import SecretRedactionFilter
from astralio.keyboards.callbacks import ALL_EXACT_CALLBACKS, CB, is_valid_callback_data
from astralio.keyboards.menus import (
    compatibility_menu_keyboard,
    forecast_menu_keyboard,
    help_menu_keyboard,
    main_menu_keyboard,
    natal_menu_keyboard,
    premium_menu_keyboard,
    profile_menu_keyboard,
    tarot_menu_keyboard,
    tarot_question_keyboard,
    wizard_nav_keyboard,
)
from tests.conftest import FakeFirestoreClient


def _collect_registered_callback_patterns(app: object) -> list[re.Pattern[str]]:
    patterns: list[re.Pattern[str]] = []

    def _visit(handler: object) -> None:
        if isinstance(handler, CallbackQueryHandler) and handler.pattern is not None:
            if isinstance(handler.pattern, re.Pattern):
                patterns.append(handler.pattern)
            elif isinstance(handler.pattern, str):
                patterns.append(re.compile(handler.pattern))
        elif isinstance(handler, ConversationHandler):
            for ep in handler.entry_points:
                _visit(ep)
            for state_handlers in handler.states.values():
                for sh in state_handlers:
                    _visit(sh)
            for fb in handler.fallbacks:
                _visit(fb)

    for group_handlers in app.handlers.values():  # type: ignore[attr-defined]
        for h in group_handlers:
            _visit(h)
    return patterns


def test_every_keyboard_button_has_valid_registered_handler(
    test_settings: Settings,
    fake_db: FakeFirestoreClient,
) -> None:
    """Guarantee zero dead buttons: every callback_data in every keyboard matches a handler."""
    app = build_application(test_settings, firestore_client=fake_db)
    patterns = _collect_registered_callback_patterns(app)

    keyboards = [
        main_menu_keyboard(),
        natal_menu_keyboard(has_saved_birth_date=True),
        natal_menu_keyboard(has_saved_birth_date=False),
        compatibility_menu_keyboard(has_saved_birth_date=True),
        compatibility_menu_keyboard(has_saved_birth_date=False),
        forecast_menu_keyboard(has_saved_birth_date=True),
        forecast_menu_keyboard(has_saved_birth_date=False),
        tarot_menu_keyboard(),
        tarot_question_keyboard(),
        profile_menu_keyboard(),
        premium_menu_keyboard(),
        help_menu_keyboard(),
        wizard_nav_keyboard(
            extra_buttons=[
                InlineKeyboardButton("t1", callback_data=CB.NATAL_TIME_UNKNOWN),
                InlineKeyboardButton("t2", callback_data=CB.NATAL_PLACE_SKIP),
                InlineKeyboardButton("t3", callback_data=CB.COMPAT_TIME_UNKNOWN),
                InlineKeyboardButton("t4", callback_data=CB.COMPAT_PLACE_SKIP),
                InlineKeyboardButton("t5", callback_data=CB.PROFILE_TIME_UNKNOWN),
            ]
        ),
    ]

    discovered: set[str] = set()
    for kb in keyboards:
        for row in kb.inline_keyboard:
            for btn in row:
                assert btn.callback_data is not None
                discovered.add(btn.callback_data)

    # Every constant in CB must be emitted and matched
    assert discovered == set(ALL_EXACT_CALLBACKS)
    for cb_data in discovered:
        assert is_valid_callback_data(cb_data)
        assert len(cb_data.encode("utf-8")) <= 64
        assert any(p.match(cb_data) for p in patterns), f"Unhandled callback_data: {cb_data}"


def test_secret_redaction_filter_masks_tokens_and_keys() -> None:
    bot_token = "987654321:AASecretTokenValue1234567890abcd"
    private_key = "-----BEGIN PRIVATE KEY-----\nSUPERSECRETKEYDATA\n-----END PRIVATE KEY-----"
    filt = SecretRedactionFilter(secrets=[bot_token, private_key])

    record = logging.LogRecord(
        name="astralio.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Failed request https://api.telegram.org/bot%s/getMe with %s and Bearer sk-live-999",
        args=(bot_token, private_key),
        exc_info=None,
    )
    filt.filter(record)
    rendered = record.getMessage()
    assert bot_token not in rendered
    assert "SUPERSECRETKEYDATA" not in rendered
    assert "sk-live-999" not in rendered
    assert "[REDACTED" in rendered


def test_settings_validation_and_private_key_normalization() -> None:
    settings = Settings(
        BOT_TOKEN="123456:AAValidTokenFormat",
        FIREBASE_PROJECT_ID="proj-1",
        FIREBASE_CLIENT_EMAIL="svc@proj-1.iam.gserviceaccount.com",
        FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\nLINE1\\n-----END PRIVATE KEY-----\\n",
        FIREBASE_DATABASE_ID="   ",
    )
    assert settings.firebase_database_id is None
    assert "\nLINE1\n" in settings.normalized_firebase_private_key
    assert settings.has_ai_configured is False

    with pytest.raises(ValidationError):
        Settings(
            BOT_TOKEN="invalid-token-without-colon",
            FIREBASE_PROJECT_ID="proj-1",
            FIREBASE_CLIENT_EMAIL="svc@proj-1.iam.gserviceaccount.com",
            FIREBASE_PRIVATE_KEY="key",
        )


def test_private_key_normalization_handles_quotes_json_and_single_line() -> None:
    quoted = Settings(
        BOT_TOKEN="123456:AAValidTokenFormat",
        FIREBASE_PROJECT_ID="proj-1",
        FIREBASE_CLIENT_EMAIL="svc@proj-1.iam.gserviceaccount.com",
        FIREBASE_PRIVATE_KEY='"-----BEGIN PRIVATE KEY-----\\nAAAA\\nBBBB\\n-----END PRIVATE KEY-----\\n",',
    )
    assert quoted.normalized_firebase_private_key == (
        "-----BEGIN PRIVATE KEY-----\nAAAABBBB\n-----END PRIVATE KEY-----\n"
    )

    from_json = Settings(
        BOT_TOKEN="123456:AAValidTokenFormat",
        FIREBASE_PROJECT_ID="proj-1",
        FIREBASE_CLIENT_EMAIL="svc@proj-1.iam.gserviceaccount.com",
        FIREBASE_PRIVATE_KEY='{"private_key": "-----BEGIN PRIVATE KEY-----\\nCCCC\\n-----END PRIVATE KEY-----\\n"}',
    )
    assert from_json.normalized_firebase_private_key == (
        "-----BEGIN PRIVATE KEY-----\nCCCC\n-----END PRIVATE KEY-----\n"
    )


def test_storage_mode_auto_falls_back_on_invalid_firebase_key_while_firestore_is_strict(
    tmp_path: object,
) -> None:
    from pathlib import Path

    from astralio.app import build_service_container
    from astralio.infrastructure.firebase import FirebaseInitError
    from astralio.infrastructure.local_store import LocalFileFirestoreClient

    local_file = Path(str(tmp_path)) / "fallback.json"

    auto_settings = Settings(
        BOT_TOKEN="123456:AAValidTokenFormat",
        FIREBASE_PROJECT_ID="proj-1",
        FIREBASE_CLIENT_EMAIL="svc@proj-1.iam.gserviceaccount.com",
        FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nINVALID\n-----END PRIVATE KEY-----\n",
        STORAGE_MODE="auto",
        LOCAL_DB_PATH=str(local_file),
    )
    container = build_service_container(auto_settings)
    assert isinstance(container.feedback_repository._db, LocalFileFirestoreClient)

    strict_settings = Settings(
        BOT_TOKEN="123456:AAValidTokenFormat",
        FIREBASE_PROJECT_ID="proj-1",
        FIREBASE_CLIENT_EMAIL="svc@proj-1.iam.gserviceaccount.com",
        FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nINVALID\n-----END PRIVATE KEY-----\n",
        STORAGE_MODE="firestore",
        LOCAL_DB_PATH=str(local_file),
    )
    with pytest.raises(FirebaseInitError):
        build_service_container(strict_settings)
