from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ברוך הבא לתנועת אחדות!\nבחר אחת מהאפשרויות:\n1. מומחה\n2. תומך"
    )
