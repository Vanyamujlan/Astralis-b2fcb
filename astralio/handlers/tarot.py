"""Tarot spread selection, optional question wizard, card drawing, and history handlers."""

from __future__ import annotations

from telegram import Update
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
from astralio.keyboards.callbacks import CB, parse_callback_data
from astralio.keyboards.menus import tarot_menu_keyboard, tarot_question_keyboard
from astralio.models.tarot import TarotSpreadType

TAROT_WAIT_QUESTION = 0
_TAROT_SPREAD_KEY = "tarot_selected_spread"


async def show_tarot_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display available Tarot spreads and history button."""
    await ensure_user(update, context)
    context.user_data.pop(_TAROT_SPREAD_KEY, None)
    await reply_or_edit(
        update,
        "🃏 <b>Таро Astralio</b>\n\n"
        "Полная колода из 78 карт (прямое и перевёрнутое положение, без повторов внутри расклада). "
        "Каждый расклад сохраняется в вашу историю.\n\n"
        "Выберите расклад:",
        reply_markup=tarot_menu_keyboard(),
    )
    return ConversationHandler.END


async def select_tarot_spread(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask for an optional question before drawing cards."""
    await ensure_user(update, context)
    query = update.callback_query
    parsed = parse_callback_data(query.data if query else None)
    if parsed is None or parsed[2] is None:
        return await show_tarot_menu(update, context)

    try:
        spread_type = TarotSpreadType(parsed[2])
    except ValueError:
        return await show_tarot_menu(update, context)

    services = get_services(context)
    spec = services.tarot_service.get_spread_spec(spread_type)
    context.user_data[_TAROT_SPREAD_KEY] = spread_type.value

    await reply_or_edit(
        update,
        f"🃏 <b>{spec.title}</b>\n"
        f"{spec.description}\n\n"
        "Сформулируйте вопрос для расклада текстовым сообщением (до 300 символов) "
        "или нажмите «Вытянуть без вопроса»:",
        reply_markup=tarot_question_keyboard(),
    )
    return TAROT_WAIT_QUESTION


async def _execute_tarot_draw(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    question: str | None,
    prefer_new_message: bool,
) -> int:
    profile = await ensure_user(update, context)
    raw_spread = context.user_data.pop(_TAROT_SPREAD_KEY, TarotSpreadType.ONE_CARD.value)
    try:
        spread_type = TarotSpreadType(raw_spread)
    except ValueError:
        spread_type = TarotSpreadType.ONE_CARD

    services = get_services(context)
    clean_question = escape_html(question.strip()[:300]) if question and question.strip() else None

    # Draw cards first, optionally enhance summary via AI with honest local fallback
    reading = await services.tarot_service.create_and_save_reading(
        telegram_id=profile.telegram_id,
        spread_type=spread_type,
        question=clean_question,
    )

    if services.ai_service.is_enabled:
        cards_facts = "; ".join(
            f"{c.position_title}: {c.name_ru} ({'перевёрнутая' if c.is_reversed else 'прямая'})"
            for c in reading.cards
        )
        ai_res = await services.ai_service.enhance_interpretation(
            user_id=profile.telegram_id,
            system_prompt=(
                "Ты внимательный таролог. Дай связный краткий итог расклада (3-4 предложения) "
                "на русском языке строго по вытянутым картам и их позициям."
            ),
            facts_prompt=f"Расклад: {reading.spread_title}. Вопрос: {clean_question or 'общий'}. Карты: {cards_facts}.",
            local_fallback=reading.summary,
        )
        if ai_res.source == "ai" and ai_res.text:
            reading.summary = escape_html(ai_res.text)
            reading.interpretation_source = "ai"
            await services.tarot_service._reading_repo.save_tarot_reading(reading)  # noqa: SLF001

    await reply_or_edit(
        update,
        services.tarot_service.format_reading(reading),
        reply_markup=tarot_menu_keyboard(),
        prefer_new_message=prefer_new_message,
    )
    return ConversationHandler.END


async def receive_tarot_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return TAROT_WAIT_QUESTION
    return await _execute_tarot_draw(
        update,
        context,
        question=update.message.text,
        prefer_new_message=True,
    )


async def skip_tarot_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _execute_tarot_draw(
        update,
        context,
        question=None,
        prefer_new_message=False,
    )


async def show_tarot_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the user's saved Tarot readings from Firestore."""
    profile = await ensure_user(update, context)
    services = get_services(context)
    readings = await services.tarot_service.get_history(profile.telegram_id, limit=5)
    await reply_or_edit(
        update,
        services.tarot_service.format_history(readings),
        reply_markup=tarot_menu_keyboard(),
    )


def build_tarot_conversation() -> ConversationHandler:
    spread_pattern = (
        f"^({CB.TAROT_SPREAD_ONE}|{CB.TAROT_SPREAD_THREE}|"
        f"{CB.TAROT_SPREAD_REL}|{CB.TAROT_SPREAD_PATH})$"
    )
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(select_tarot_spread, pattern=spread_pattern),
        ],
        states={
            TAROT_WAIT_QUESTION: [
                CallbackQueryHandler(skip_tarot_question, pattern=f"^{CB.TAROT_SKIP_QUESTION}$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_tarot_question),
                CallbackQueryHandler(show_tarot_menu, pattern=f"^{CB.NAV_BACK}$"),
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
        name="tarot_spread_conversation",
    )


def register_tarot_handlers(app: Application) -> None:
    app.add_handler(build_tarot_conversation())
    app.add_handler(CallbackQueryHandler(show_tarot_menu, pattern=f"^{CB.MENU_TAROT}$"))
    app.add_handler(CallbackQueryHandler(show_tarot_history, pattern=f"^{CB.TAROT_HISTORY}$"))
