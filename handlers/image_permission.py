from telegram.ext import CommandHandler, ContextTypes
from telegram import Update
from core.permissions import request_permission

async def request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request_permission(update.effective_user)

    await update.message.reply_text("בקשתך נשלחה לאדמין.")

permission_request_handler = CommandHandler("request_image_access", request)
