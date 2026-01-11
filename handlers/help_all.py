from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 פקודות הבוט:\n\n"
        "/start – התחלה\n"
        "/register – הרשמה\n"
        "/expert – תפריט אקספרט\n"
        "/approve – אישור משתמש (אדמין)\n"
        "/all – רשימת פקודות מלאה\n"
        "📷 שליחת תמונה – עריכה (מורשים בלבד)"
    )

all_handler = CommandHandler("all", all_cmd)
