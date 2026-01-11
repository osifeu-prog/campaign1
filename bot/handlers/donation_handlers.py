# bot/handlers/donation_handlers.py
# ===============================
# תרומות TON - מקלדת, callbacks ובדיקת סטטוס
# ===============================

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from utils.constants import TON_WALLET_ADDRESS, MIN_DONATION_AMOUNT, LOG_GROUP_ID
from services.logger_service import log
from bot.core.telemetry import telemetry

def build_donation_keyboard() -> InlineKeyboardMarkup:
    """
    בניית מקלדת תרומות עם קישורים ל‑Tonkeeper ופעולות נוספות.
    """
    ton_link = f"ton://transfer/{TON_WALLET_ADDRESS}"
    buttons = [
        [InlineKeyboardButton(f"💎 לתרום {MIN_DONATION_AMOUNT} TON", url=f"{ton_link}?amount={int(MIN_DONATION_AMOUNT * 1e9)}")],
        [InlineKeyboardButton("💎 לתרום 5 TON", url=f"{ton_link}?amount={int(5 * 1e9)}")],
        [InlineKeyboardButton("💎 לתרום 10 TON", url=f"{ton_link}?amount={int(10 * 1e9)}")],
        [InlineKeyboardButton("💎 לתרום סכום מותאם אישית", url=ton_link)],
        [InlineKeyboardButton("📋 העתקת כתובת ארנק", callback_data="copy_wallet")],
        [InlineKeyboardButton("ℹ️ מה זה TON?", callback_data="ton_info")],
        [InlineKeyboardButton("🔙 חזרה לתפריט ראשי", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)

async def handle_donation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    טיפול בלחיצה על כפתור 'לתרום' מתוך התפריט.
    מציג הסבר, כתובת ארנק ומקלדת עם אפשרויות.
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user

    await log(context, "Donation page opened", user=user)
    await telemetry.track_event(context, "donation_page_view", user=user)

    text = (
        "💎 תמיכה בתנועת אחדות דרך TON\n\n"
        "תרומתך עוזרת לנו:\n"
        "• להפעיל את הבוט ואת המערכת\n"
        "• לקיים אירועים ופעילויות\n"
        "• לפתח כלים נוספים לקהילה\n\n"
        f"כתובת הארנק שלנו:\n`{TON_WALLET_ADDRESS}`\n\n"
        "בחר סכום או העתק את הכתובת למרכת הטון שלך:"
    )

    keyboard = build_donation_keyboard()
    await query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def handle_copy_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    הצגת הכתובת להעתקה (תגובה על לחצן).
    """
    query = update.callback_query
    await query.answer("כתובת הארנק הועתקה!", show_alert=False)
    await query.message.reply_text(
        f"כתובת הארנק שלנו:\n\n`{TON_WALLET_ADDRESS}`\n\n"
        "לחץ על הכתובת כדי להעתיק",
        parse_mode="Markdown"
    )

async def handle_ton_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    הסבר קצר על TON והוראות לתרומה.
    """
    query = update.callback_query
    await query.answer()
    text = (
        "ℹ️ מה זה TON?\n\n"
        "TON (The Open Network) הוא בלוקצ'יין מהיר ומאובטח שפותח על ידי Telegram.\n\n"
        "איך לתרום:\n"
        "1️⃣ הורד את אפליקציית Tonkeeper או ארנק TON אחר\n"
        "2️⃣ קנה TON דרך האפליקציה או העבר מארנק אחר\n"
        "3️⃣ לחץ על אחד הכפתורים למעלה או העתק את כתובת הארנק\n"
        "4️⃣ שלח את התרומה!\n\n"
        "נקבל הודעה על התרומה ונודה לך אישית 💙"
    )
    await query.message.reply_text(text)

async def check_donation_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    בדיקת סטטוס תרומות (פקודה לאדמינים) - מציג קישורים והנחיות.
    """
    from bot.flows.menu_flow import is_admin

    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    text = (
        "📊 סטטוס תרומות:\n\n"
        f"כתובת ארנק: `{TON_WALLET_ADDRESS}`\n\n"
        "לצפייה בתרומות בפועל:\n"
        "1. היכנס ל‑Tonkeeper או Tonscan\n"
        f"2. חפש את הכתובת: {TON_WALLET_ADDRESS}\n"
        "3. צפה בהיסטוריית העסקאות\n\n"
        "🔗 Tonscan: https://tonscan.org/address/" + TON_WALLET_ADDRESS
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def notify_donation_received(context: ContextTypes.DEFAULT_TYPE, amount: float, sender: str = "Unknown"):
    """
    שליחת הודעה לקבוצת לוג על תרומה שהתקבלה.
    (דורש אינטגרציה חיצונית עם TON API כדי לפעול אוטומטית)
    """
    if not LOG_GROUP_ID:
        return

    text = (
        "💎 תרומה חדשה התקבלה!\n\n"
        f"סכום: {amount} TON\n"
        f"שולח: {sender}\n"
        f"זמן: {datetime.utcnow().isoformat()}\n\n"
        "תודה רבה לתורם! 💙"
    )
    try:
        await context.bot.send_message(chat_id=int(LOG_GROUP_ID), text=text)
    except Exception as e:
        print(f"Failed to send donation notification: {e}")
