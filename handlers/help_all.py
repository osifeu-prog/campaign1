from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start – התחלה\n"
        "/ALL – כל הפקודות\n"
    )

all_handler = CommandHandler("ALL", all_cmd)
