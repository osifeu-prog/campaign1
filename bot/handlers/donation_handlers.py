# bot/handlers/donation_handlers.py
# ==========================================
# תרומות TON – הצגת ארנק, העתקה, מידע
# ==========================================

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from utils.constants import (
    TON_WALLET_ADDRESS,
    CALLBACK_DONATE,
    CALLBACK_COPY_WALLET,
    CALLBACK_TON_INFO,
)
from services.logger_service import log


async def handle_donation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "💎 תמיכה בתנועת אחדות דרך TON\n\n"
        "תרומתך עוזרת לנו:\n"
        "• להפעיל את הבוט ואת המערכת\n"
        "• לקיים אירועים ופעילויות\n"
        "• לפתח כלים נוספים לקהילה\n\n"
        "כתובת הארנק שלנו:\n"
        f"{TON_WALLET_ADDRESS}\n\n"
        "בחר סכום או העתק את הכתובת:"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 העתק כתובת", callback_data=CALLBACK_COPY_WALLET)],
        [InlineKeyboardButton("ℹ️ מה זה TON?", callback_data=CALLBACK_TON_INFO)],
    ])

    await query.message.reply_text(text, reply_markup=keyboard)
    await log(context, "Donation page opened", user=query.from_user)


async def handle_copy_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        f"כתובת הארנק:\n{TON_WALLET_ADDRESS}\n\n"
        "לחץ על הכתובת כדי להעתיק."
    )


async def handle_ton_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "ℹ️ מה זה TON?\n\n"
        "TON (The Open Network) הוא בלוקצ'יין מהיר ומאובטח שפותח על ידי Telegram.\n\n"
        "איך לתרום:\n"
        "1️⃣ הורד את אפליקציית Tonkeeper או ארנק TON אחר\n"
        "2️⃣ קנה TON דרך האפליקציה או העבר מארנק אחר\n"
        "3️⃣ העתק את כתובת הארנק שלנו ושלח את התרומה\n\n"
        "נודה לך אישית על כל תמיכה 💙"
    )

    await query.message.reply_text(text)
