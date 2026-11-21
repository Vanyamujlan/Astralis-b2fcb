"""Profile view and step-by-step birth data editing handlers."""

from __future__ import annotations

from telegram import InlineKeyboardButton, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from astralio.handlers.common import cancel_operation, menu_command, start_command
from astralio.handlers.deps import ensure_user, escape_html, get_services, reply_or_edit
from astralio.keyboards.callbacks import CB
from astralio.keyboards.menus import profile_menu_keyboard, wizard_nav_keyboard
from astralio.services.validators import InputValidationError, parse_birth_date, parse_birth_time

PROFILE_WAIT_DATE, PROFILE_WAIT_TIME, PROFILE_WAIT_PLACE = range(3)


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the user's current profile and edit options."""
    profile = await ensure_user(update, context)
    services = get_services(context)
    await reply_or_edit(
        update,
        services.user_service.format_profile(profile),
        reply_markup=profile_menu_keyboard(),
    )
    return ConversationHandler.END


async def start_edit_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await ensure_user(update, context)
    await reply_or_edit(
        update,
        "📅 <b>Изменение даты рождения</b>\n\n"
        "Введите дату рождения в формате <code>ДД.ММ.ГГГГ</code> (например, <code>15.05.1995</code>):",
        reply_markup=wizard_nav_keyboard(include_back=True),
    )
    return PROFILE_WAIT_DATE


async def receive_edit_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return PROFILE_WAIT_DATE
    try:
        parsed_date = parse_birth_date(update.message.text)
    except InputValidationError as exc:
        await reply_or_edit(
            update,
            f"⚠️ {exc}\n\nПопробуйте снова (формат <code>ДД.ММ.ГГГГ</code>):",
            reply_markup=wizard_nav_keyboard(include_back=True),
            prefer_new_message=True,
        )
        return PROFILE_WAIT_DATE

    user = await ensure_user(update, context)
    services = get_services(context)
    updated = await services.user_service.update_birth_date(user.telegram_id, parsed_date)
    await reply_or_edit(
        update,
        f"✅ Дата рождения обновлена: <b>{parsed_date.strftime('%d.%m.%Y')}</b>\n\n"
        + services.user_service.format_profile(updated),
        reply_markup=profile_menu_keyboard(),
        prefer_new_message=True,
    )
    return ConversationHandler.END


async def start_edit_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await ensure_user(update, context)
    await reply_or_edit(
        update,
        "🕒 <b>Изменение времени рождения</b>\n\n"
        "Введите время рождения в формате <code>ЧЧ:ММ</code> (например, <code>14:30</code>) "
        "или нажмите кнопку ниже, если точное время неизвестно:",
        reply_markup=wizard_nav_keyboard(
            extra_buttons=[
                InlineKeyboardButton("🤷 Время неизвестно", callback_data=CB.PROFILE_TIME_UNKNOWN)
            ],
            include_back=True,
        ),
    )
    return PROFILE_WAIT_TIME


async def receive_edit_time_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = await ensure_user(update, context)
    services = get_services(context)
    updated = await services.user_service.update_birth_time(
        user.telegram_id,
        None,
        is_unknown=True,
    )
    await reply_or_edit(
        update,
        "✅ Сохранено: <b>время рождения неизвестно</b> "
        "(при расчёте карты Асцендент и дома не будут вычисляться).\n\n"
        + services.user_service.format_profile(updated),
        reply_markup=profile_menu_keyboard(),
    )
    return ConversationHandler.END


async def receive_edit_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return PROFILE_WAIT_TIME
    try:
        parsed_time, is_unknown = parse_birth_time(update.message.text)
    except InputValidationError as exc:
        await reply_or_edit(
            update,
            f"⚠️ {exc}",
            reply_markup=wizard_nav_keyboard(
                extra_buttons=[
                    InlineKeyboardButton(
                        "🤷 Время неизвестно", callback_data=CB.PROFILE_TIME_UNKNOWN
                    )
                ],
                include_back=True,
            ),
            prefer_new_message=True,
        )
        return PROFILE_WAIT_TIME

    user = await ensure_user(update, context)
    services = get_services(context)
    updated = await services.user_service.update_birth_time(
        user.telegram_id,
        parsed_time,
        is_unknown=is_unknown,
    )
    label = "неизвестно" if is_unknown or parsed_time is None else parsed_time.strftime("%H:%M")
    await reply_or_edit(
        update,
        f"✅ Время рождения обновлено: <b>{label}</b>\n\n"
        + services.user_service.format_profile(updated),
        reply_markup=profile_menu_keyboard(),
        prefer_new_message=True,
    )
    return ConversationHandler.END


async def start_edit_place(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await ensure_user(update, context)
    await reply_or_edit(
        update,
        "📍 <b>Изменение места рождения</b>\n\n"
        "Введите город рождения (например, <code>Москва</code>, <code>Алматы</code>, <code>Берлин</code>) "
        "или координаты в формате <code>широта, долгота</code> (например, <code>55.7558, 37.6173</code>):",
        reply_markup=wizard_nav_keyboard(include_back=True),
    )
    return PROFILE_WAIT_PLACE


async def receive_edit_place(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return PROFILE_WAIT_PLACE
    raw_place = update.message.text.strip()
    user = await ensure_user(update, context)
    services = get_services(context)
    location = await services.user_service.resolve_place(raw_place)
    if location is None:
        await reply_or_edit(
            update,
            f"⚠️ Не удалось определить координаты для «{escape_html(raw_place)}».\n"
            "Уточните название города (например, <code>Санкт-Петербург</code>) или укажите "
            "координаты в формате <code>55.7558, 37.6173</code>:",
            reply_markup=wizard_nav_keyboard(include_back=True),
            prefer_new_message=True,
        )
        return PROFILE_WAIT_PLACE

    updated = await services.user_service.update_birth_place(user.telegram_id, location)
    await reply_or_edit(
        update,
        f"✅ Место рождения обновлено: <b>{escape_html(location.name)}</b> "
        f"({location.latitude:.2f}, {location.longitude:.2f}, {location.timezone})\n\n"
        + services.user_service.format_profile(updated),
        reply_markup=profile_menu_keyboard(),
        prefer_new_message=True,
    )
    return ConversationHandler.END


def build_profile_conversation() -> ConversationHandler:
    """Create ConversationHandler for editing user profile fields."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_edit_date, pattern=f"^{CB.PROFILE_EDIT_DATE}$"),
            CallbackQueryHandler(start_edit_time, pattern=f"^{CB.PROFILE_EDIT_TIME}$"),
            CallbackQueryHandler(start_edit_place, pattern=f"^{CB.PROFILE_EDIT_PLACE}$"),
        ],
        states={
            PROFILE_WAIT_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_date),
                CallbackQueryHandler(show_profile, pattern=f"^{CB.NAV_BACK}$"),
            ],
            PROFILE_WAIT_TIME: [
                CallbackQueryHandler(
                    receive_edit_time_unknown,
                    pattern=f"^{CB.PROFILE_TIME_UNKNOWN}$",
                ),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_time),
                CallbackQueryHandler(show_profile, pattern=f"^{CB.NAV_BACK}$"),
            ],
            PROFILE_WAIT_PLACE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_place),
                CallbackQueryHandler(show_profile, pattern=f"^{CB.NAV_BACK}$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_operation, pattern=f"^{CB.NAV_CANCEL}$"),
            CallbackQueryHandler(menu_command, pattern=f"^{CB.MENU_MAIN}$"),
            CommandHandler("start", start_command),
            CommandHandler("cancel", cancel_operation),
            CommandHandler("menu", menu_command),
        ],
        allow_reentry=True,
        per_message=False,
        name="profile_edit_conversation",
    )


def register_profile_handlers(app: Application) -> None:
    app.add_handler(build_profile_conversation())
    app.add_handler(CallbackQueryHandler(show_profile, pattern=f"^{CB.MENU_PROFILE}$"))
