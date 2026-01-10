# bot/handlers/bot_handlers.py
# ==========================================
# ראוטר מרכזי – /start, /menu, /help, states
# ==========================================

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

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
from bot.flows import start_flow, menu_flow
from bot.handlers import supporter_handlers, expert_handlers


# ===============================
# Commands
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_flow.handle_start(update, context)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_flow.handle_menu_command(update, context)


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_flow.handle_menu_callback(update, context)


async def all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 רשימת פקודות:\n\n"
        "/start – התחלה\n"
        "/menu – תפריט ראשי\n"
        "/leaderboard – טבלת מובילים\n"
        "/myid – הצגת user_id\n"
        "/groupid – הצגת group_id\n"
        "/positions – רשימת מקומות (admin)\n"
        "/help – עזרה\n"
    )
    await update.message.reply_text(text)


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"user_id שלך: {update.effective_user.id}")


async def group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ("group", "supergroup"):
        await update.message.reply_text(f"group_id: {chat.id}")
    else:
        await update.message.reply_text("יש להריץ את הפקודה בתוך קבוצה.")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("
