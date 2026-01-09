# ===============================
# זרימת תומך (Supporter flow)
# ===============================

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from bot.states import (
    SUPPORTER_NAME,
    SUPPORTER_CITY,
    SUPPORTER_EMAIL,
    SUPPORTER_PHONE,
    SUPPORTER_FEEDBACK,
)
from utils.constants import ROLE_SUPPORTER
from services import sheets_service
from services.logger_service import log


def build_personal_link(bot_username: str, user_id: int) -> str:
    """
    בניית קישור אישי לתומך
    """
    return f"https://t.me/{bot_username}?start={user_id}"


async def supporter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_full_name"] = update.message.text.strip()
    await log(context, "Supporter name entered", user=update.effective_user)
    await update.message.reply_text("באיזו עיר אתה גר?")
    return SUPPORTER_CITY


async def supporter_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_city"] = update.message.text.strip()
    await log(context, "Supporter city entered", user=update.effective_user)
    await update.message.reply_text("כתובת אימייל (אפשר 'דלג'):")
    return SUPPORTER_EMAIL


async def supporter_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["supporter_email"] = "" if text.lower() in ["דלג", "skip"] else text

    await log(context, "Supporter email entered", user=update.effective_user)
    await update.message.reply_text("מה מספר הטלפון שלך?")
    return SUPPORTER_PHONE


async def supporter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_phone"] = update.message.text.strip()
    await log(context, "Supporter phone entered", user=update.effective_user)
    await update.message.reply_text("מה גרם לך להצטרף לתנועה?")
    return SUPPORTER_FEEDBACK


async def supporter_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_feedback"] = update.message.text.strip()

    user_row = {
        "user_id": context.user_data.get("user_id"),
        "username": context.user_data.get("username"),
        "full_name_telegram": context.user_data.get("full_name_telegram"),
        "role": ROLE_SUPPORTER,
        "city": context.user_data.get("supporter_city"),
        "email": context.user_data.get("supporter_email"),
        "referrer": context.user_data.get("referrer", ""),
        "joined_via_expert_id": context.user_data.get("joined_via_expert_id", ""),
        "created_at": context.user_data.get("created_at"),
    }

    sheets_service.append_user_row(user_row)
    await log(context, "Supporter registered", user=update.effective_user)

    personal_link = build_personal_link(context.bot.username, context.user_data["user_id"])

    text = (
        "תודה שנרשמת כתומך! 🙌\n\n"
        "זהו קישור אישי שתוכל לשתף עם חברים ומשפחה:\n"
        f"{personal_link}\n\n"
        "מה תרצה לעשות עכשיו?"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 לשתף את הקישור שלי", url=personal_link)],
        [InlineKeyboardButton("🧠 להגיש מועמדות כמומחה", callback_data="apply_expert_again")],
        [InlineKeyboardButton("📋 פתיחת תפריט ראשי", callback_data="menu_main")],
    ])

    await update.message.reply_text(text, reply_markup=keyboard)
    return ConversationHandler.END
