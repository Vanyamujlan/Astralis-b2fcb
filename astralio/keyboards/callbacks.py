"""Centralized callback_data constants and validation helpers."""

from __future__ import annotations


class CB:
    """Namespace of all valid Astralio inline keyboard callback_data tokens."""

    # Global navigation
    MENU_MAIN = "menu:main"
    NAV_CANCEL = "nav:cancel"
    NAV_BACK = "nav:back"

    # Top-level 7 modules
    MENU_NATAL = "menu:natal"
    MENU_COMPAT = "menu:compat"
    MENU_FORECAST = "menu:forecast"
    MENU_TAROT = "menu:tarot"
    MENU_PROFILE = "menu:profile"
    MENU_PREMIUM = "menu:premium"
    MENU_HELP = "menu:help"

    # Natal chart actions
    NATAL_FROM_PROFILE = "natal:from_profile"
    NATAL_NEW = "natal:new"
    NATAL_TIME_UNKNOWN = "natal:time_unknown"
    NATAL_PLACE_SKIP = "natal:place_skip"

    # Compatibility actions
    COMPAT_USE_PROFILE = "compat:use_profile"
    COMPAT_MANUAL = "compat:manual"
    COMPAT_TIME_UNKNOWN = "compat:time_unknown"
    COMPAT_PLACE_SKIP = "compat:place_skip"

    # Forecast actions
    FORECAST_DAILY = "forecast:daily"
    FORECAST_WEEKLY = "forecast:weekly"

    # Tarot actions
    TAROT_SPREAD_ONE = "tarot:spread:one_card"
    TAROT_SPREAD_THREE = "tarot:spread:three_cards"
    TAROT_SPREAD_REL = "tarot:spread:relationship"
    TAROT_SPREAD_PATH = "tarot:spread:path_choice"
    TAROT_SKIP_QUESTION = "tarot:skip_question"
    TAROT_HISTORY = "tarot:history"

    # Profile actions
    PROFILE_EDIT_DATE = "profile:edit_date"
    PROFILE_EDIT_TIME = "profile:edit_time"
    PROFILE_EDIT_PLACE = "profile:edit_place"
    PROFILE_TIME_UNKNOWN = "profile:time_unknown"

    # Premium actions
    PREMIUM_STATUS = "premium:status"
    PREMIUM_BUY_MONTHLY = "premium:buy:monthly"
    PREMIUM_BUY_QUARTERLY = "premium:buy:quarterly"
    PREMIUM_BUY_YEARLY = "premium:buy:yearly"

    # Help actions
    HELP_GUIDE = "help:guide"
    HELP_FEEDBACK = "help:feedback"


ALL_EXACT_CALLBACKS: frozenset[str] = frozenset(
    value for key, value in vars(CB).items() if not key.startswith("_") and isinstance(value, str)
)


def is_valid_callback_data(data: str | None) -> bool:
    """Validate incoming callback_data against the strict allowlist."""
    if not data or len(data.encode("utf-8")) > 64:
        return False
    return data in ALL_EXACT_CALLBACKS


def parse_callback_data(data: str | None) -> tuple[str, str, str | None] | None:
    """Parse a validated callback token into `(namespace, action, param)`."""
    if not is_valid_callback_data(data):
        return None
    assert data is not None
    parts = data.split(":")
    if len(parts) == 2:
        return parts[0], parts[1], None
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    return None
