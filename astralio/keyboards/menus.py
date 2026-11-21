"""Minimalist InlineKeyboardMarkup builders for Astralio."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from astralio.keyboards.callbacks import CB


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main Astralio menu with all 7 core sections."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✨ Натальная карта", callback_data=CB.MENU_NATAL),
                InlineKeyboardButton("💞 Совместимость", callback_data=CB.MENU_COMPAT),
            ],
            [
                InlineKeyboardButton("🔮 Прогнозы", callback_data=CB.MENU_FORECAST),
                InlineKeyboardButton("🃏 Таро", callback_data=CB.MENU_TAROT),
            ],
            [
                InlineKeyboardButton("👤 Профиль", callback_data=CB.MENU_PROFILE),
                InlineKeyboardButton("⭐ Premium", callback_data=CB.MENU_PREMIUM),
            ],
            [
                InlineKeyboardButton("❓ Помощь", callback_data=CB.MENU_HELP),
            ],
        ]
    )


def natal_menu_keyboard(*, has_saved_birth_date: bool) -> InlineKeyboardMarkup:
    """Natal chart submenu."""
    rows: list[list[InlineKeyboardButton]] = []
    if has_saved_birth_date:
        rows.append(
            [
                InlineKeyboardButton(
                    "✨ Рассчитать по моему профилю",
                    callback_data=CB.NATAL_FROM_PROFILE,
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                "📝 Ввести данные рождения",
                callback_data=CB.NATAL_NEW,
            )
        ]
    )
    rows.append([InlineKeyboardButton("⬅️ Главное меню", callback_data=CB.MENU_MAIN)])
    return InlineKeyboardMarkup(rows)


def compatibility_menu_keyboard(*, has_saved_birth_date: bool) -> InlineKeyboardMarkup:
    """Compatibility submenu."""
    rows: list[list[InlineKeyboardButton]] = []
    if has_saved_birth_date:
        rows.append(
            [
                InlineKeyboardButton(
                    "💞 Мой профиль + партнёр",
                    callback_data=CB.COMPAT_USE_PROFILE,
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                "📝 Ввести данные двух людей",
                callback_data=CB.COMPAT_MANUAL,
            )
        ]
    )
    rows.append([InlineKeyboardButton("⬅️ Главное меню", callback_data=CB.MENU_MAIN)])
    return InlineKeyboardMarkup(rows)


def forecast_menu_keyboard(*, has_saved_birth_date: bool) -> InlineKeyboardMarkup:
    """Forecast submenu."""
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton("🌅 Прогноз на сегодня", callback_data=CB.FORECAST_DAILY),
            InlineKeyboardButton("🗓 Прогноз на неделю", callback_data=CB.FORECAST_WEEKLY),
        ]
    ]
    if not has_saved_birth_date:
        rows.append(
            [
                InlineKeyboardButton(
                    "📝 Заполнить данные рождения",
                    callback_data=CB.NATAL_NEW,
                )
            ]
        )
    rows.append([InlineKeyboardButton("⬅️ Главное меню", callback_data=CB.MENU_MAIN)])
    return InlineKeyboardMarkup(rows)


def tarot_menu_keyboard() -> InlineKeyboardMarkup:
    """Tarot spreads & history submenu."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎴 Карта дня (1 карта)", callback_data=CB.TAROT_SPREAD_ONE)],
            [
                InlineKeyboardButton(
                    "⏳ Прошлое · Настоящее · Будущее (3)",
                    callback_data=CB.TAROT_SPREAD_THREE,
                )
            ],
            [InlineKeyboardButton("💞 Отношения (3 карты)", callback_data=CB.TAROT_SPREAD_REL)],
            [InlineKeyboardButton("🧭 Выбор пути (5 карт)", callback_data=CB.TAROT_SPREAD_PATH)],
            [InlineKeyboardButton("📚 История раскладов", callback_data=CB.TAROT_HISTORY)],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data=CB.MENU_MAIN)],
        ]
    )


def tarot_question_keyboard() -> InlineKeyboardMarkup:
    """Navigation keyboard during optional Tarot question prompt."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🃏 Вытянуть без вопроса", callback_data=CB.TAROT_SKIP_QUESTION)],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data=CB.NAV_BACK),
                InlineKeyboardButton("✖️ Отмена", callback_data=CB.NAV_CANCEL),
            ],
        ]
    )


def profile_menu_keyboard() -> InlineKeyboardMarkup:
    """Profile view and editing keyboard."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📅 Изменить дату рождения", callback_data=CB.PROFILE_EDIT_DATE)],
            [
                InlineKeyboardButton(
                    "🕒 Изменить время рождения", callback_data=CB.PROFILE_EDIT_TIME
                )
            ],
            [
                InlineKeyboardButton(
                    "📍 Изменить место рождения", callback_data=CB.PROFILE_EDIT_PLACE
                )
            ],
            [
                InlineKeyboardButton(
                    "✨ Открыть натальную карту", callback_data=CB.NATAL_FROM_PROFILE
                )
            ],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data=CB.MENU_MAIN)],
        ]
    )


def premium_menu_keyboard() -> InlineKeyboardMarkup:
    """Premium tariffs & subscription status keyboard."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⭐ 1 месяц — 199 Stars", callback_data=CB.PREMIUM_BUY_MONTHLY)],
            [
                InlineKeyboardButton(
                    "⭐ 3 месяца — 499 Stars", callback_data=CB.PREMIUM_BUY_QUARTERLY
                )
            ],
            [InlineKeyboardButton("⭐ 1 год — 1499 Stars", callback_data=CB.PREMIUM_BUY_YEARLY)],
            [InlineKeyboardButton("🔍 Проверить статус подписки", callback_data=CB.PREMIUM_STATUS)],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data=CB.MENU_MAIN)],
        ]
    )


def help_menu_keyboard() -> InlineKeyboardMarkup:
    """Help instructions & feedback keyboard."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📖 Инструкция по функциям", callback_data=CB.HELP_GUIDE)],
            [InlineKeyboardButton("✉️ Оставить обратную связь", callback_data=CB.HELP_FEEDBACK)],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data=CB.MENU_MAIN)],
        ]
    )


def wizard_nav_keyboard(
    *,
    extra_buttons: list[InlineKeyboardButton] | None = None,
    include_back: bool = True,
) -> InlineKeyboardMarkup:
    """Reusable step-by-step wizard keyboard with Back and Cancel controls."""
    rows: list[list[InlineKeyboardButton]] = []
    if extra_buttons:
        for btn in extra_buttons:
            rows.append([btn])
    nav_row: list[InlineKeyboardButton] = []
    if include_back:
        nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=CB.NAV_BACK))
    nav_row.append(InlineKeyboardButton("✖️ Отмена", callback_data=CB.NAV_CANCEL))
    rows.append(nav_row)
    return InlineKeyboardMarkup(rows)
