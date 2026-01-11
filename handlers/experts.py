from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.sheets_service import get_sheet

async def expert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    sheet = get_sheet("Users")
    users = sheet.get_all_records()

    for u in users:
        if u["user_id"] == user_id and u["role"] == "expert":
            await update.message.reply_text(
                "🎓 תפריט אקספרט:\n"
                "• צפייה בבקשות\n"
                "• עדכון סטטוס\n"
            )
            return

    await update.message.reply_text("⛔️ אין לך הרשאת אקספרט")

expert_handler = CommandHandler("expert", expert)
