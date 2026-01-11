from telegram import Update
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("אין לך הרשאות ניהול.")
        return

    await update.message.reply_text(
        "תפריט ניהול:\n"
        "- אישור מומחים\n"
        "- ניהול משתמשים\n"
        "- צפייה בלוגים\n\n"
        "(הרחבות נוספות בפיתוח)"
    )
