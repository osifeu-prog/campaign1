
from telegram.ext import Application
from config.settings import TELEGRAM_BOT_TOKEN


def build_application() -> Application:
    return Application.builder().token(TELEGRAM_BOT_TOKEN).build()

bot/handlers/common.py

from telegram import Update
from telegram.ext import ContextTypes
from services.sheets import append_row


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ברוכים הבאים לשער האזרחי הרשמי.\n\n"
        "מערכת זו נועדה לרישום אזרחים ומומחים, "
        "בבסיס תשתית אזרחית-טכנולוגית שקופה ואחראית."
    )

    append_row(
        "Logs",
        [update.effective_user.id, "start", update.effective_user.username],
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/register – רישום אזרח\n"
        "/expert – בקשת הצטרפות כמומחה\n"
        "/status – בדיקת סטטוס\n"
        "/admin – ניהול (לאדמינים בלבד)"
    )

bot/handlers/user.py

from telegram import Update
from telegram.ext import ContextTypes
from services.sheets import append_row


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    append_row(
        "Users",
        [user.id, user.full_name, user.username],
    )

    await update.message.reply_text(
        "הרישום האזרחי נקלט בהצלחה.\n"
        "תודה על הצטרפותך."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "הפרופיל שלך קיים במערכת.\n"
        "לעדכונים נוספים – פנה לאדמיניסטרציה."
    )
