from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.sheets_service import get_sheet
import os

ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("שימוש: /approve <user_id>")
        return

    user_id = context.args[0]
    sheet = get_sheet("Users")
    records = sheet.get_all_records()

    for idx, row in enumerate(records, start=2):
        if str(row["user_id"]) == user_id:
            sheet.update_cell(idx, 4, "approved")
            await update.message.reply_text(f"✅ משתמש {user_id} אושר")
            return

    await update.message.reply_text("❌ משתמש לא נמצא")

approve_handler = CommandHandler("approve", approve)
