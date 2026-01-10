# bot/handlers/bot_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.states import (
    SUPPORTER_NAME,
    SUPPORTER_CITY,
    SUPPORTER_EMAIL,
    SUPPORTER_PHONE,
    SUPPORTER_FEEDBACK,
    EXPERT_NAME,
    EXPERT_FIELD,
    EXPERT_EXPERIENCE,
    EXPERT_POSITION,
    EXPERT_LINKS,
    EXPERT_WHY,
)

from bot.flows import start_flow, menu_flow
from bot.handlers import supporter_handlers, expert_handlers


# ===============================
# עזר לתפריט תחתון
# ===============================

def footer_keyboard(rows):
    footer = [InlineKeyboardButton("📋 פקודות", callback_data="show_all_commands")]
    rows.append(footer)
    return InlineKeyboardMarkup(rows)

def main_menu_keyboard():
    rows = [
        [InlineKeyboardButton("הגש מועמדות כמומחה", callback_data="apply_expert")],
        [InlineKeyboardButton("הרשם כתומך", callback_data="apply_supporter")],
        [InlineKeyboardButton("טבלת מובילים", callback_data="leaderboard")],
    ]
    return footer_keyboard(rows)

# ===============================
# /start – קרוסלת פתיחה (start_flow)
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start – מפעיל את הקרוסלה וה‑flow המלא מתוך start_flow.
    """
    await start_flow.handle_start(update, context)

# ===============================
# /menu – תפריט ראשי (menu_flow)
# ===============================

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /menu – מפעיל את תפריט המשתמש מתוך menu_flow.
    """
    await menu_flow.handle_menu_command(update, context)

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    router לכל callbackי התפריט (menu_flow).
    """
    await menu_flow.handle_menu_callback(update, context)

# ===============================
# /help – רשימת פקודות
# ===============================

async def all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 רשימת פקודות ותפריטים מלאה:\n\n"
        "/start  התחלה (קרוסלת פתיחה)\n"
        "/menu  תפריט ראשי\n"
        "/leaderboard  טבלת מובילים\n"
        "/myid  הצגת ה‑user_id שלך\n"
        "/groupid  הצגת group id (בקבוצה)\n"
        "/positions  רשימת מקומות (admin)\n"
        "/validate_sheets  בדיקת Google Sheets (admin)\n"
        "/fix_sheets  תיקון אוטומטי של גיליונות (admin)\n"
        "/backup_sheets  גיבוי גיליונות (admin)\n"
        "/clear_user_duplicates  הסרת כפילויות תומכים (admin)\n"
        "/clear_expert_duplicates  הסרת כפילויות מומחים (admin)\n"
        "/broadcast_supporters  שידור לתומכים (admin)\n"
        "/broadcast_experts  שידור למומחים (admin)\n"
        "/dashboard  סטטיסטיקות בסיסיות (admin)\n"
        "/help  עזרה\n\n"
        "תפריטים אינטראקטיביים מופיעים תחת /menu או באמצעות הכפתורים שבהודעות."
    )
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text)
            await update.callback_query.answer()
            return
        except Exception:
            pass
    await update.message.reply_text(text)

# ===============================
# /myid, /groupid
# ===============================

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"user_id שלך: `{user.id}`", parse_mode="Markdown")

async def group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ("group", "supergroup", "channel"):
        await update.message.reply_text(f"group id: `{chat.id}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("את הפקודה /groupid יש להריץ בתוך קבוצה או סופר־קבוצה.")

# ===============================
# Unknown command
# ===============================

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("הפקודה הזו לא מוכרת.\nנסה /menu כדי לראות את כל האפשרויות.")

# ===============================
# Wrappers ל‑supporter/expert flows (ConversationHandler)
# ===============================

# תומך – עוטף את supporter_handlers כך שה‑states יתאימו ל‑bot.states

async def supporter_name_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await supporter_handlers.supporter_name(update, context)
    return SUPPORTER_CITY

async def supporter_city_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await supporter_handlers.supporter_city(update, context)
    return SUPPORTER_EMAIL

async def supporter_email_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await supporter_handlers.supporter_email(update, context)
    return SUPPORTER_PHONE

async def supporter_phone_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await supporter_handlers.supporter_phone(update, context)
    return SUPPORTER_FEEDBACK

async def supporter_feedback_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await supporter_handlers.supporter_feedback(update, context)
    # סוף ה־flow
    return ConversationHandler.END

# מומחה – מחובר ישירות ל‑expert_handlers (הוא כבר משתמש ב‑bot.states)

async def expert_name_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await expert_handlers.expert_name(update, context)

async def expert_field_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await expert_handlers.expert_field(update, context)

async def expert_experience_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await expert_handlers.expert_experience(update, context)

async def expert_position_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await expert_handlers.expert_position(update, context)

async def expert_links_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await expert_handlers.expert_links(update, context)

async def expert_why_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await expert_handlers.expert_why(update, context)

# ===============================
# ConversationHandler ראשי
# ===============================

def get_conversation_handler():
    """
    ConversationHandler שמכסה:
    - /start  (start_flow)
    - הרשמת תומך  (supporter_handlers)
    - הרשמת מומחה (expert_handlers)
    """
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # תומך
            SUPPORTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_name_state)],
            SUPPORTER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_city_state)],
            SUPPORTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_email_state)],
            SUPPORTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_phone_state)],
            SUPPORTER_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_feedback_state)],
            # מומחה
            EXPERT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_name_state)],
            EXPERT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_field_state)],
            EXPERT_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_experience_state)],
            EXPERT_POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_position_state)],
            EXPERT_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_links_state)],
            EXPERT_WHY: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_why_state)],
        },
        fallbacks=[
            CommandHandler("help", all_commands),
        ],
        per_message=False,
    )
    return conv

# ===============================
# Backwards-compatible alias for start callbacks (קרוסלה)
# ===============================

def handle_start_callback_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Alias כדי ש-main.py יוכל לרשום CallbackQueryHandler לקרוסלת /start.
    """
    # start_flow.handle_start_callback הוא async – צריך להחזיר coroutine
    return start_flow.handle_start_callback(update, context)
