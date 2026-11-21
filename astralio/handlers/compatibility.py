"""Compatibility (synastry) menu and step-by-step two-person wizard."""

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
from astralio.keyboards.menus import compatibility_menu_keyboard, wizard_nav_keyboard
from astralio.models.user import BirthData
from astralio.services.validators import (
    InputValidationError,
    parse_birth_date,
    parse_birth_time,
    parse_person_name,
)

(
    COMPAT_P1_NAME,
    COMPAT_P1_DATE,
    COMPAT_P1_TIME,
    COMPAT_P1_PLACE,
    COMPAT_P2_NAME,
    COMPAT_P2_DATE,
    COMPAT_P2_TIME,
    COMPAT_P2_PLACE,
) = range(8)

_COMPAT_DRAFT_KEY = "compat_draft"


async def show_compatibility_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the Compatibility section menu."""
    profile = await ensure_user(update, context)
    has_date = profile.birth_data.has_birth_date
    hint = (
        "Рассчитаем астрологическую совместимость по реальным положениям планет двух людей."
        if has_date
        else "Введите данные двух людей, чтобы рассчитать синастрическую совместимость."
    )
    await reply_or_edit(
        update,
        f"💞 <b>Совместимость (синастрия)</b>\n\n{hint}",
        reply_markup=compatibility_menu_keyboard(has_saved_birth_date=has_date),
    )
    return ConversationHandler.END


async def start_compat_with_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Use saved user profile as Person 1 and jump straight to Person 2."""
    profile = await ensure_user(update, context)
    if not profile.birth_data.has_birth_date:
        await reply_or_edit(
            update,
            "В профиле ещё не указана дата рождения. Начнём с ввода данных первого человека.",
            reply_markup=compatibility_menu_keyboard(has_saved_birth_date=False),
        )
        return ConversationHandler.END

    context.user_data[_COMPAT_DRAFT_KEY] = {
        "from_profile": True,
        "p1_name": profile.display_name,
        "p1_birth": profile.birth_data,
    }
    await _prompt_p2_name(update, prefer_new_message=False)
    return COMPAT_P2_NAME


async def start_compat_manual(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start full manual input for Person 1 and Person 2."""
    await ensure_user(update, context)
    context.user_data[_COMPAT_DRAFT_KEY] = {"from_profile": False}
    await _prompt_p1_name(update, prefer_new_message=False)
    return COMPAT_P1_NAME


async def _prompt_p1_name(update: Update, *, prefer_new_message: bool = False) -> None:
    await reply_or_edit(
        update,
        "💞 <b>Совместимость — Человек 1 (шаг 1/4)</b>\n\nВведите имя первого человека:",
        reply_markup=wizard_nav_keyboard(include_back=True),
        prefer_new_message=prefer_new_message,
    )


async def _prompt_p1_date(update: Update, *, prefer_new_message: bool = False) -> None:
    await reply_or_edit(
        update,
        "📅 <b>Человек 1 (шаг 2/4)</b>\n\nВведите дату рождения (<code>ДД.ММ.ГГГГ</code>):",
        reply_markup=wizard_nav_keyboard(include_back=True),
        prefer_new_message=prefer_new_message,
    )


async def _prompt_p1_time(update: Update, *, prefer_new_message: bool = False) -> None:
    await reply_or_edit(
        update,
        "🕒 <b>Человек 1 (шаг 3/4)</b>\n\nВведите время рождения (<code>ЧЧ:ММ</code>) "
        "или нажмите «Время неизвестно»:",
        reply_markup=wizard_nav_keyboard(
            extra_buttons=[
                InlineKeyboardButton("🤷 Время неизвестно", callback_data=CB.COMPAT_TIME_UNKNOWN)
            ],
            include_back=True,
        ),
        prefer_new_message=prefer_new_message,
    )


async def _prompt_p1_place(update: Update, *, prefer_new_message: bool = False) -> None:
    await reply_or_edit(
        update,
        "📍 <b>Человек 1 (шаг 4/4)</b>\n\nВведите город рождения или нажмите «Пропустить»:",
        reply_markup=wizard_nav_keyboard(
            extra_buttons=[
                InlineKeyboardButton("⏭ Пропустить место", callback_data=CB.COMPAT_PLACE_SKIP)
            ],
            include_back=True,
        ),
        prefer_new_message=prefer_new_message,
    )


async def _prompt_p2_name(update: Update, *, prefer_new_message: bool = False) -> None:
    await reply_or_edit(
        update,
        "💞 <b>Совместимость — Партнёр (шаг 1/4)</b>\n\nВведите имя второго человека:",
        reply_markup=wizard_nav_keyboard(include_back=True),
        prefer_new_message=prefer_new_message,
    )


async def _prompt_p2_date(update: Update, *, prefer_new_message: bool = False) -> None:
    await reply_or_edit(
        update,
        "📅 <b>Партнёр (шаг 2/4)</b>\n\nВведите дату рождения партнёра (<code>ДД.ММ.ГГГГ</code>):",
        reply_markup=wizard_nav_keyboard(include_back=True),
        prefer_new_message=prefer_new_message,
    )


async def _prompt_p2_time(update: Update, *, prefer_new_message: bool = False) -> None:
    await reply_or_edit(
        update,
        "🕒 <b>Партнёр (шаг 3/4)</b>\n\nВведите время рождения партнёра (<code>ЧЧ:ММ</code>) "
        "или нажмите «Время неизвестно»:",
        reply_markup=wizard_nav_keyboard(
            extra_buttons=[
                InlineKeyboardButton("🤷 Время неизвестно", callback_data=CB.COMPAT_TIME_UNKNOWN)
            ],
            include_back=True,
        ),
        prefer_new_message=prefer_new_message,
    )


async def _prompt_p2_place(update: Update, *, prefer_new_message: bool = False) -> None:
    await reply_or_edit(
        update,
        "📍 <b>Партнёр (шаг 4/4)</b>\n\nВведите город рождения партнёра или нажмите «Пропустить»:",
        reply_markup=wizard_nav_keyboard(
            extra_buttons=[
                InlineKeyboardButton("⏭ Пропустить место", callback_data=CB.COMPAT_PLACE_SKIP)
            ],
            include_back=True,
        ),
        prefer_new_message=prefer_new_message,
    )


# --- Person 1 handlers ---


async def recv_p1_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return COMPAT_P1_NAME
    try:
        name = parse_person_name(update.message.text)
    except InputValidationError as exc:
        await reply_or_edit(
            update,
            f"⚠️ {exc}",
            reply_markup=wizard_nav_keyboard(include_back=True),
            prefer_new_message=True,
        )
        return COMPAT_P1_NAME
    context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})["p1_name"] = name
    await _prompt_p1_date(update, prefer_new_message=True)
    return COMPAT_P1_DATE


async def recv_p1_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return COMPAT_P1_DATE
    try:
        parsed_date = parse_birth_date(update.message.text)
    except InputValidationError as exc:
        await reply_or_edit(
            update,
            f"⚠️ {exc}",
            reply_markup=wizard_nav_keyboard(include_back=True),
            prefer_new_message=True,
        )
        return COMPAT_P1_DATE
    context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})["p1_date"] = parsed_date
    await _prompt_p1_time(update, prefer_new_message=True)
    return COMPAT_P1_TIME


async def recv_p1_time_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return COMPAT_P1_TIME
    try:
        parsed_time, is_unknown = parse_birth_time(update.message.text)
    except InputValidationError as exc:
        await reply_or_edit(
            update,
            f"⚠️ {exc}",
            reply_markup=wizard_nav_keyboard(
                extra_buttons=[
                    InlineKeyboardButton(
                        "🤷 Время неизвестно", callback_data=CB.COMPAT_TIME_UNKNOWN
                    )
                ],
                include_back=True,
            ),
            prefer_new_message=True,
        )
        return COMPAT_P1_TIME
    draft = context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})
    draft["p1_time"] = parsed_time
    draft["p1_time_unknown"] = is_unknown
    await _prompt_p1_place(update, prefer_new_message=True)
    return COMPAT_P1_PLACE


async def recv_p1_time_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})
    draft["p1_time"] = None
    draft["p1_time_unknown"] = True
    await _prompt_p1_place(update, prefer_new_message=False)
    return COMPAT_P1_PLACE


async def recv_p1_place_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return COMPAT_P1_PLACE
    raw_place = update.message.text.strip()
    services = get_services(context)
    location = await services.user_service.resolve_place(raw_place)
    if location is None:
        await reply_or_edit(
            update,
            f"⚠️ Город «{escape_html(raw_place)}» не найден. Уточните название, введите координаты "
            "или нажмите «Пропустить место»:",
            reply_markup=wizard_nav_keyboard(
                extra_buttons=[
                    InlineKeyboardButton("⏭ Пропустить место", callback_data=CB.COMPAT_PLACE_SKIP)
                ],
                include_back=True,
            ),
            prefer_new_message=True,
        )
        return COMPAT_P1_PLACE

    draft = context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})
    draft["p1_birth"] = BirthData(
        birth_date=draft["p1_date"],
        birth_time=draft.get("p1_time"),
        birth_time_unknown=bool(draft.get("p1_time_unknown", False)),
        birth_place=location.name,
        latitude=location.latitude,
        longitude=location.longitude,
        timezone=location.timezone,
    )
    await _prompt_p2_name(update, prefer_new_message=True)
    return COMPAT_P2_NAME


async def recv_p1_place_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})
    draft["p1_birth"] = BirthData(
        birth_date=draft["p1_date"],
        birth_time=draft.get("p1_time"),
        birth_time_unknown=bool(draft.get("p1_time_unknown", False)),
    )
    await _prompt_p2_name(update, prefer_new_message=False)
    return COMPAT_P2_NAME


# --- Person 2 handlers ---


async def recv_p2_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return COMPAT_P2_NAME
    try:
        name = parse_person_name(update.message.text)
    except InputValidationError as exc:
        await reply_or_edit(
            update,
            f"⚠️ {exc}",
            reply_markup=wizard_nav_keyboard(include_back=True),
            prefer_new_message=True,
        )
        return COMPAT_P2_NAME
    context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})["p2_name"] = name
    await _prompt_p2_date(update, prefer_new_message=True)
    return COMPAT_P2_DATE


async def recv_p2_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return COMPAT_P2_DATE
    try:
        parsed_date = parse_birth_date(update.message.text)
    except InputValidationError as exc:
        await reply_or_edit(
            update,
            f"⚠️ {exc}",
            reply_markup=wizard_nav_keyboard(include_back=True),
            prefer_new_message=True,
        )
        return COMPAT_P2_DATE
    context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})["p2_date"] = parsed_date
    await _prompt_p2_time(update, prefer_new_message=True)
    return COMPAT_P2_TIME


async def recv_p2_time_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return COMPAT_P2_TIME
    try:
        parsed_time, is_unknown = parse_birth_time(update.message.text)
    except InputValidationError as exc:
        await reply_or_edit(
            update,
            f"⚠️ {exc}",
            reply_markup=wizard_nav_keyboard(
                extra_buttons=[
                    InlineKeyboardButton(
                        "🤷 Время неизвестно", callback_data=CB.COMPAT_TIME_UNKNOWN
                    )
                ],
                include_back=True,
            ),
            prefer_new_message=True,
        )
        return COMPAT_P2_TIME
    draft = context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})
    draft["p2_time"] = parsed_time
    draft["p2_time_unknown"] = is_unknown
    await _prompt_p2_place(update, prefer_new_message=True)
    return COMPAT_P2_PLACE


async def recv_p2_time_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})
    draft["p2_time"] = None
    draft["p2_time_unknown"] = True
    await _prompt_p2_place(update, prefer_new_message=False)
    return COMPAT_P2_PLACE


async def recv_p2_place_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return COMPAT_P2_PLACE
    raw_place = update.message.text.strip()
    services = get_services(context)
    location = await services.user_service.resolve_place(raw_place)
    if location is None:
        await reply_or_edit(
            update,
            f"⚠️ Город «{escape_html(raw_place)}» не найден. Уточните название, введите координаты "
            "или нажмите «Пропустить место»:",
            reply_markup=wizard_nav_keyboard(
                extra_buttons=[
                    InlineKeyboardButton("⏭ Пропустить место", callback_data=CB.COMPAT_PLACE_SKIP)
                ],
                include_back=True,
            ),
            prefer_new_message=True,
        )
        return COMPAT_P2_PLACE

    draft = context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})
    p2_birth = BirthData(
        birth_date=draft["p2_date"],
        birth_time=draft.get("p2_time"),
        birth_time_unknown=bool(draft.get("p2_time_unknown", False)),
        birth_place=location.name,
        latitude=location.latitude,
        longitude=location.longitude,
        timezone=location.timezone,
    )
    return await _finish_compatibility(update, context, p2_birth, prefer_new_message=True)


async def recv_p2_place_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = context.user_data.setdefault(_COMPAT_DRAFT_KEY, {})
    p2_birth = BirthData(
        birth_date=draft["p2_date"],
        birth_time=draft.get("p2_time"),
        birth_time_unknown=bool(draft.get("p2_time_unknown", False)),
    )
    return await _finish_compatibility(update, context, p2_birth, prefer_new_message=False)


async def _finish_compatibility(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    p2_birth: BirthData,
    *,
    prefer_new_message: bool,
) -> int:
    profile = await ensure_user(update, context)
    draft = context.user_data.pop(_COMPAT_DRAFT_KEY, {})
    services = get_services(context)

    report = services.compatibility_service.calculate_compatibility(
        person_a_name=escape_html(draft["p1_name"]),
        person_a_birth=draft["p1_birth"],
        person_b_name=escape_html(draft["p2_name"]),
        person_b_birth=p2_birth,
    )
    ai_res = await services.ai_service.enhance_interpretation(
        user_id=profile.telegram_id,
        system_prompt=(
            "Ты деликатный астролог по синастрии. Напиши краткую рекомендацию (3-4 предложения) "
            "на русском языке строго на основе переданных показателей совместимости."
        ),
        facts_prompt=(
            f"Общая совместимость: {report.overall_score}%, эмоции: {report.emotional_score}%, "
            f"романтика: {report.romance_score}%, общение: {report.communication_score}%. "
            f"Сильные стороны: {'; '.join(report.strengths[:2])}. "
            f"Зоны роста: {'; '.join(report.challenges[:2])}."
        ),
        local_fallback=report.advice,
    )
    extra = escape_html(ai_res.text) if ai_res.source == "ai" else ai_res.text
    text = services.compatibility_service.format_compatibility_report(report, extra_summary=extra)
    await reply_or_edit(
        update,
        text,
        reply_markup=compatibility_menu_keyboard(
            has_saved_birth_date=profile.birth_data.has_birth_date
        ),
        prefer_new_message=prefer_new_message,
    )
    return ConversationHandler.END


# --- Step-by-step Back navigation ---


async def compat_back_to_p1_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _prompt_p1_name(update, prefer_new_message=False)
    return COMPAT_P1_NAME


async def compat_back_to_p1_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _prompt_p1_date(update, prefer_new_message=False)
    return COMPAT_P1_DATE


async def compat_back_to_p1_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _prompt_p1_time(update, prefer_new_message=False)
    return COMPAT_P1_TIME


async def compat_back_from_p2_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = context.user_data.get(_COMPAT_DRAFT_KEY, {})
    if draft.get("from_profile"):
        return await show_compatibility_menu(update, context)
    await _prompt_p1_place(update, prefer_new_message=False)
    return COMPAT_P1_PLACE


async def compat_back_to_p2_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _prompt_p2_name(update, prefer_new_message=False)
    return COMPAT_P2_NAME


async def compat_back_to_p2_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _prompt_p2_date(update, prefer_new_message=False)
    return COMPAT_P2_DATE


async def compat_back_to_p2_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _prompt_p2_time(update, prefer_new_message=False)
    return COMPAT_P2_TIME


def build_compatibility_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_compat_with_profile, pattern=f"^{CB.COMPAT_USE_PROFILE}$"),
            CallbackQueryHandler(start_compat_manual, pattern=f"^{CB.COMPAT_MANUAL}$"),
        ],
        states={
            COMPAT_P1_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_p1_name),
                CallbackQueryHandler(show_compatibility_menu, pattern=f"^{CB.NAV_BACK}$"),
            ],
            COMPAT_P1_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_p1_date),
                CallbackQueryHandler(compat_back_to_p1_name, pattern=f"^{CB.NAV_BACK}$"),
            ],
            COMPAT_P1_TIME: [
                CallbackQueryHandler(recv_p1_time_unknown, pattern=f"^{CB.COMPAT_TIME_UNKNOWN}$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_p1_time_text),
                CallbackQueryHandler(compat_back_to_p1_date, pattern=f"^{CB.NAV_BACK}$"),
            ],
            COMPAT_P1_PLACE: [
                CallbackQueryHandler(recv_p1_place_skip, pattern=f"^{CB.COMPAT_PLACE_SKIP}$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_p1_place_text),
                CallbackQueryHandler(compat_back_to_p1_time, pattern=f"^{CB.NAV_BACK}$"),
            ],
            COMPAT_P2_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_p2_name),
                CallbackQueryHandler(compat_back_from_p2_name, pattern=f"^{CB.NAV_BACK}$"),
            ],
            COMPAT_P2_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_p2_date),
                CallbackQueryHandler(compat_back_to_p2_name, pattern=f"^{CB.NAV_BACK}$"),
            ],
            COMPAT_P2_TIME: [
                CallbackQueryHandler(recv_p2_time_unknown, pattern=f"^{CB.COMPAT_TIME_UNKNOWN}$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_p2_time_text),
                CallbackQueryHandler(compat_back_to_p2_date, pattern=f"^{CB.NAV_BACK}$"),
            ],
            COMPAT_P2_PLACE: [
                CallbackQueryHandler(recv_p2_place_skip, pattern=f"^{CB.COMPAT_PLACE_SKIP}$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, recv_p2_place_text),
                CallbackQueryHandler(compat_back_to_p2_time, pattern=f"^{CB.NAV_BACK}$"),
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
        name="compatibility_conversation",
    )


def register_compatibility_handlers(app: Application) -> None:
    app.add_handler(build_compatibility_conversation())
    app.add_handler(CallbackQueryHandler(show_compatibility_menu, pattern=f"^{CB.MENU_COMPAT}$"))
