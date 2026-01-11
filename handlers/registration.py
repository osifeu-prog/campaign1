from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.sheets_service import get_sheet

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    sheet = get_sheet("Users")

    users = sheet.col_values(1)
    if str(user.id) in users:
        await update.message.reply_text("✅ אתה כבר רשום במערכת")
        return

    sheet.append_row([
        str(user.id),
        user.username or "",
        "user",
        "pending"
    ])

    await update.message.reply_text(
        "📝 נרשמת בהצלחה!\nההרשאה תיבדק ע\"י אדמין."
    )

register_handler = CommandHandler("register", register)
