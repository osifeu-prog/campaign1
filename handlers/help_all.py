from telegram.ext import CommandHandler, ContextTypes
from telegram import Update

async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start – התחלה\n"
        "/ALL – כל הפקודות\n"
        "שליחת תמונה – כלי התאמת רזולוציה (בהרשאה)"
    )

all_handler = CommandHandler("ALL", all_cmd)
