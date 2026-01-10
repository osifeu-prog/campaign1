# ===============================
# bot_handlers – Router ראשי
# ===============================

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot import supporter_handlers, expert_handlers
from bot.states import (
    SUPPORTER_NAME,
    SUPPORTER_CITY,
    SUPPORTER_EMAIL,
    SUPPORTER_PHONE,
    SUPPORTER_FEEDBACK,
    EXPERT_NAME,
    EXPERT_FIELD,
    EXPERT_EXPERIENCE,
    EXPERT_POSITION,
    EXPERT_LINKS,
    EXPERT_WHY,
)
from bot.start_flow import handle_start, handle_start_callback
from bot.menu_flow import handle_menu_command, handle_menu_callback
from bot.session_manager import session_manager
from bot.locale_service import locale_service
from bot.telemetry import telemetry
from services.logger_service import log
from utils.constants import (
    CALLBACK_START_SLIDE,
    CALLBACK_START_SOCI,
    CALLBACK_START_FINISH,
)


# ===============================
# פקודות כלליות
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_start(update, context)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_menu_command(update, context)


async def all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log(context, "All commands requested", user=update.effective_user)
    text = (
        "/start – התחלה מחדש\n"
        "/menu – פתיחת תפריט ראשי\n"
        "/help – רשימת פקודות\n"
        "/myid – הצגת ה־user_id שלך\n"
        "/groupid – הצגת group id (בקבוצה)\n"
    )
    await update.message.reply_text(text)


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await log(context, "my_id requested", user=update.effective_user)
    await update.message.reply_text(f"user_id שלך: {user_id}")


async def group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await log(context, "group_id requested", user=update.effective_user, extra={"chat_id": chat.id})
    await update.message.reply_text(f"group/chat id: {chat.id}")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = locale_service.detect_language(user.language_code)
    await log(context, "Unknown command", user=user, extra={"text": update.message.text})
    await update.message.reply_text(locale_service.t("unknown_command", lang=lang))


# ===============================
# קרוסלת /start – callback handler
# ===============================

async def handle_start_callback_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_start_callback(update, context)


# ===============================
# ConversationHandler הראשי
# ===============================

def get_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[],
        states={
            SUPPORTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_handlers.supporter_name)],
            SUPPORTER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_handlers.supporter_city)],
            SUPPORTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_handlers.supporter_email)],
            SUPPORTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_handlers.supporter_phone)],
            SUPPORTER_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_handlers.supporter_feedback)],

            EXPERT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_name)],
            EXPERT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_field)],
            EXPERT_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_experience)],
            EXPERT_POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_position)],
            EXPERT_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_links)],
            EXPERT_WHY: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_why)],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("menu", menu_command),
        ],
    )
