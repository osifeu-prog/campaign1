# bot/handlers/bot_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        update_id = getattr(update, "update_id", None)
        if update_id is not None:
            last = context.chat_data.get("last_handled_update_id")
            if last == update_id:
                return
            context.chat_data["last_handled_update_id"] = update_id
    except Exception:
        pass

    text = (
        "ברוך הבא לתנועת אחדות.\n\n"
        "אני הבוט שדרכו מצטרפים, נרשמים כתומכים ומגישים מועמדות כמומחים.\n\n"
        "איך תרצה להצטרף?"
    )
    kb = main_menu_keyboard()
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=kb)
            await update.callback_query.answer()
            return
        except Exception:
            pass
    await update.message.reply_text(text, reply_markup=kb)

async def all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 רשימת פקודות ותפריטים מלאה:\n\n"
        "/start  התחלה\n"
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
        "/help  עזרה\n\n"
        "תפריטים אינטראקטיביים מופיעים תחת /menu. ניתן גם להשתמש בכפתורים בתוך ההודעות."
    )
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text)
            await update.callback_query.answer()
            return
        except Exception:
            pass
    await update.message.reply_text(text)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("הפקודה הזו לא מוכרת.\nנסה /menu כדי לראות את כל האפשרויות.")

def get_conversation_handler():
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={},
        fallbacks=[CommandHandler("help", all_commands)],
        per_message=False,
    )
    return conv
