"""Natal chart menu, instant calculation from profile, and step-by-step birth data wizard."""

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
from astralio.keyboards.menus import natal_menu_keyboard, wizard_nav_keyboard
from astralio.models.user import BirthData
from astralio.services.validators import InputValidationError, parse_birth_date, parse_birth_time

NATAL_DATE, NATAL_TIME, NATAL_PLACE = range(3)
_NATAL_DRAFT_KEY = "natal_draft"


async def show_natal_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the Natal Chart section menu."""
    profile = await ensure_user(update, context)
    has_date = profile.birth_data.has_birth_date
    hint = (
        "Вы можете рассчитать карту по сохранённым данным профиля или ввести новые данные рождения."
        if has_date
        else "Для расчёта натальной карты введите дату, время (если известно) и место рождения."
    )
    await reply_or_edit(
        update,
        f"✨ <b>Натальная карта</b>\n\n{hint}",
        reply_markup=natal_menu_keyboard(has_saved_birth_date=has_date),
    )
    return ConversationHandler.END


async def _render_natal_chart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    birth_data: BirthData,
    subject_name: str,
    *,
    prefer_new_message: bool = False,
) -> None:
    services = get_services(context)
    chart = services.astrology_service.calculate_natal_chart(
        birth_data,
        subject_name=escape_html(subject_name),
    )
    local_interp = services.astrology_service.build_local_interpretation(chart)
    planets_facts = ", ".join(
        f"{p.name_ru}: {p.sign_ru} {p.degree_in_sign:.1f}°" for p in chart.planets[:7]
    )
    asc_fact = (
        f", Асцендент: {chart.ascendant.sign_ru}"
        if chart.ascendant
        else ", Асцендент: не рассчитан"
    )
    ai_res = await services.ai_service.enhance_interpretation(
        user_id=update.effective_user.id if update.effective_user else 0,
        system_prompt=(
            "Ты деликатный астролог-аналитик. Дай краткую структурированную интерпретацию (4-5 предложений) "
            "на русском языке строго по переданным астрономическим положениям без выдумывания новых позиций."
        ),
        facts_prompt=f"Положения карты: {planets_facts}{asc_fact}. Доминирующая стихия: {chart.dominant_element}.",
        local_fallback=local_interp,
    )
    interpretation = escape_html(ai_res.text) if ai_res.source == "ai" else ai_res.text
    text = services.astrology_service.format_natal_chart(chart, interpretation=interpretation)
    await reply_or_edit(
        update,
        text,
        reply_markup=natal_menu_keyboard(has_saved_birth_date=True),
        prefer_new_message=prefer_new_message,
    )


async def calculate_natal_from_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Immediately compute natal chart from saved profile birth data."""
    profile = await ensure_user(update, context)
    if not profile.birth_data.has_birth_date:
        await reply_or_edit(
            update,
            "В вашем профиле пока не указана дата рождения. Введите данные рождения шаг за шагом:",
            reply_markup=natal_menu_keyboard(has_saved_birth_date=False),
        )
        return ConversationHandler.END

    await _render_natal_chart(update, context, profile.birth_data, profile.display_name)
    return ConversationHandler.END


async def start_natal_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 1: ask for birth date."""
    await ensure_user(update, context)
    context.user_data[_NATAL_DRAFT_KEY] = {}
    await reply_or_edit(
        update,
        "✨ <b>Натальная карта — шаг 1 из 3</b>\n\n"
        "Введите дату рождения в формате <code>ДД.ММ.ГГГГ</code> (например, <code>15.05.1995</code>):",
        reply_markup=wizard_nav_keyboard(include_back=True),
    )
    return NATAL_DATE


async def natal_receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return NATAL_DATE
    try:
        parsed_date = parse_birth_date(update.message.text)
    except InputValidationError as exc:
        await reply_or_edit(
            update,
            f"⚠️ {exc}\n\nВведите дату рождения (например, <code>15.05.1995</code>):",
            reply_markup=wizard_nav_keyboard(include_back=True),
            prefer_new_message=True,
        )
        return NATAL_DATE

    draft = context.user_data.setdefault(_NATAL_DRAFT_KEY, {})
    draft["birth_date"] = parsed_date
    await _prompt_natal_time(update, prefer_new_message=True)
    return NATAL_TIME


async def _prompt_natal_time(update: Update, *, prefer_new_message: bool = False) -> None:
    await reply_or_edit(
        update,
        "🕒 <b>Натальная карта — шаг 2 из 3</b>\n\n"
        "Введите точное время рождения в формате <code>ЧЧ:ММ</code> (например, <code>14:30</code>).\n"
        "Если время неизвестно, нажмите кнопку ниже — мы рассчитаем планеты и явно укажем ограничения:",
        reply_markup=wizard_nav_keyboard(
            extra_buttons=[
                InlineKeyboardButton("🤷 Время неизвестно", callback_data=CB.NATAL_TIME_UNKNOWN)
            ],
            include_back=True,
        ),
        prefer_new_message=prefer_new_message,
    )


async def natal_receive_time_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return NATAL_TIME
    try:
        parsed_time, is_unknown = parse_birth_time(update.message.text)
    except InputValidationError as exc:
        await reply_or_edit(
            update,
            f"⚠️ {exc}",
            reply_markup=wizard_nav_keyboard(
                extra_buttons=[
                    InlineKeyboardButton("🤷 Время неизвестно", callback_data=CB.NATAL_TIME_UNKNOWN)
                ],
                include_back=True,
            ),
            prefer_new_message=True,
        )
        return NATAL_TIME

    draft = context.user_data.setdefault(_NATAL_DRAFT_KEY, {})
    draft["birth_time"] = parsed_time
    draft["birth_time_unknown"] = is_unknown
    await _prompt_natal_place(update, prefer_new_message=True)
    return NATAL_PLACE


async def natal_receive_time_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = context.user_data.setdefault(_NATAL_DRAFT_KEY, {})
    draft["birth_time"] = None
    draft["birth_time_unknown"] = True
    await _prompt_natal_place(update, prefer_new_message=False)
    return NATAL_PLACE


async def _prompt_natal_place(update: Update, *, prefer_new_message: bool = False) -> None:
    await reply_or_edit(
        update,
        "📍 <b>Натальная карта — шаг 3 из 3</b>\n\n"
        "Введите город рождения (например, <code>Москва</code>, <code>Казань</code>, <code>Лондон</code>) "
        "или координаты <code>широта, долгота</code>.\n"
        "Место рождения необходимо для расчёта Асцендента, домов и часового пояса:",
        reply_markup=wizard_nav_keyboard(
            extra_buttons=[
                InlineKeyboardButton(
                    "⏭ Пропустить место рождения", callback_data=CB.NATAL_PLACE_SKIP
                )
            ],
            include_back=True,
        ),
        prefer_new_message=prefer_new_message,
    )


async def natal_receive_place_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return NATAL_PLACE
    raw_place = update.message.text.strip()
    services = get_services(context)
    location = await services.user_service.resolve_place(raw_place)
    if location is None:
        await reply_or_edit(
            update,
            f"⚠️ Не удалось найти координаты для «{escape_html(raw_place)}».\n"
            "Попробуйте указать крупный ближайший город, координаты <code>55.7558, 37.6173</code> "
            "или нажмите «Пропустить место рождения»:",
            reply_markup=wizard_nav_keyboard(
                extra_buttons=[
                    InlineKeyboardButton(
                        "⏭ Пропустить место рождения",
                        callback_data=CB.NATAL_PLACE_SKIP,
                    )
                ],
                include_back=True,
            ),
            prefer_new_message=True,
        )
        return NATAL_PLACE

    return await _finish_natal_wizard(
        update,
        context,
        birth_place=location.name,
        latitude=location.latitude,
        longitude=location.longitude,
        timezone=location.timezone,
        prefer_new_message=True,
    )


async def natal_skip_place(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _finish_natal_wizard(
        update,
        context,
        birth_place=None,
        latitude=None,
        longitude=None,
        timezone=None,
        prefer_new_message=False,
    )


async def _finish_natal_wizard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    birth_place: str | None,
    latitude: float | None,
    longitude: float | None,
    timezone: str | None,
    prefer_new_message: bool,
) -> int:
    profile = await ensure_user(update, context)
    draft = context.user_data.pop(_NATAL_DRAFT_KEY, {})
    birth_data = BirthData(
        birth_date=draft["birth_date"],
        birth_time=draft.get("birth_time"),
        birth_time_unknown=bool(draft.get("birth_time_unknown", False)),
        birth_place=birth_place,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
    )
    services = get_services(context)
    await services.user_service.save_birth_data(profile.telegram_id, birth_data)
    await _render_natal_chart(
        update,
        context,
        birth_data,
        profile.display_name,
        prefer_new_message=prefer_new_message,
    )
    return ConversationHandler.END


async def natal_back_to_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await reply_or_edit(
        update,
        "✨ <b>Натальная карта — шаг 1 из 3</b>\n\n"
        "Введите дату рождения в формате <code>ДД.ММ.ГГГГ</code> (например, <code>15.05.1995</code>):",
        reply_markup=wizard_nav_keyboard(include_back=True),
    )
    return NATAL_DATE


async def natal_back_to_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _prompt_natal_time(update, prefer_new_message=False)
    return NATAL_TIME


def build_natal_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_natal_wizard, pattern=f"^{CB.NATAL_NEW}$"),
        ],
        states={
            NATAL_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, natal_receive_date),
                CallbackQueryHandler(show_natal_menu, pattern=f"^{CB.NAV_BACK}$"),
            ],
            NATAL_TIME: [
                CallbackQueryHandler(
                    natal_receive_time_unknown, pattern=f"^{CB.NATAL_TIME_UNKNOWN}$"
                ),
                MessageHandler(filters.TEXT & ~filters.COMMAND, natal_receive_time_text),
                CallbackQueryHandler(natal_back_to_date, pattern=f"^{CB.NAV_BACK}$"),
            ],
            NATAL_PLACE: [
                CallbackQueryHandler(natal_skip_place, pattern=f"^{CB.NATAL_PLACE_SKIP}$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, natal_receive_place_text),
                CallbackQueryHandler(natal_back_to_time, pattern=f"^{CB.NAV_BACK}$"),
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
        name="natal_chart_conversation",
    )


def register_natal_handlers(app: Application) -> None:
    app.add_handler(build_natal_conversation())
    app.add_handler(CallbackQueryHandler(show_natal_menu, pattern=f"^{CB.MENU_NATAL}$"))
    app.add_handler(
        CallbackQueryHandler(calculate_natal_from_profile, pattern=f"^{CB.NATAL_FROM_PROFILE}$")
    )
