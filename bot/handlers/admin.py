from telegram import Update
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS
from services.sheets import append_row


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ אין לך הרשאות ניהול.")
        return

    append_row(
        "Logs",
        [user.id, "admin_menu"],
    )

    await update.message.reply_text(
        "🛠 תפריט ניהול\n\n"
        "• אישור / דחיית מומחים\n"
        "• ניהול משתמשים\n"
        "• צפייה בלוגים\n\n"
        "מערכת זו נבנתה להתרחבות עתידית."
    )
