# bot/handlers/expert_handlers.py
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from bot.states import (
    EXPERT_NAME,
    EXPERT_FIELD,
    EXPERT_EXPERIENCE,
    EXPERT_POSITION,
    EXPERT_LINKS,
    EXPERT_WHY,
)
from utils.constants import (
    ROLE_EXPERT,
    CALLBACK_MENU_MAIN,
    CALLBACK_MENU_EXPERT,
    LOG_GROUP_ID,
    MAX_POSITIONS,
)
from services import sheets_service
from services.logger_service import log

def build_expert_referral_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start=expert_{user_id}"

async def expert_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_full_name"] = update.message.text.strip()
    await log(context, "Expert full name entered", user=update.effective_user, extra={
        "expert_full_name": context.user_data["expert_full_name"]
    })
    await update.message.reply_text("מה תחום המומחיות שלך?")
    return EXPERT_FIELD

async def expert_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_field"] = update.message.text.strip()
    await log(context, "Expert field entered", user=update.effective_user, extra={
        "expert_field": context.user_data["expert_field"]
    })
    await update.message.reply_text("ספר בקצרה על הניסיון שלך:")
    return EXPERT_EXPERIENCE

async def expert_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_experience"] = update.message.text.strip()
    await log(context, "Expert experience entered", user=update.effective_user, extra={
        "expert_experience": context.user_data["expert_experience"]
    })
    await update.message.reply_text(f"על איזה מספר מקום מתוך {MAX_POSITIONS} תרצה להתמודד?")
    return EXPERT_POSITION

async def expert_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text(f"נא להכניס מספר בין 1 ל-{MAX_POSITIONS}.")
        return EXPERT_POSITION

    pos_num = int(text)
    if not (1 <= pos_num <= MAX_POSITIONS):
        await update.message.reply_text(f"נא לבחור מספר מקום בין 1 ל-{MAX_POSITIONS}.")
        return EXPERT_POSITION

    if not sheets_service.position_is_free(str(pos_num)):
        await update.message.reply_text("המקום שבחרת תפוס. בחר מספר אחר.")
        return EXPERT_POSITION

    context.user_data["expert_position"] = str(pos_num)

    if "created_at" not in context.user_data:
        context.user_data["created_at"] = datetime.utcnow().isoformat()

    sheets_service.assign_position(
        position_id=str(pos_num),
        user_id=str(context.user_data.get("user_id")),
        timestamp=context.user_data.get("created_at"),
    )

    await log(context, "Expert position chosen and assigned", user=update.effective_user, extra={
        "position_id": pos_num
    })

    await update.message.reply_text(
        "המקום נרשם עבורך.\n"
        "הוסף קישורים (לינקדאין, אתר, מאמרים):"
    )
    return EXPERT_LINKS

async def expert_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_links"] = update.message.text.strip()
    await log(context, "Expert links entered", user=update.effective_user, extra={
        "expert_links": context.user_data["expert_links"]
    })
    await update.message.reply_text("כתוב כמה משפטים עליך:")
    return EXPERT_WHY

async def expert_why(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_why"] = update.message.text.strip()

    if len(context.user_data["expert_why"]) < 20:
        await update.message.reply_text("נשמח לכמה משפטים נוספים (לפחות 20 תווים).")
        return EXPERT_WHY

    if "created_at" not in context.user_data:
        context.user_data["created_at"] = datetime.utcnow().isoformat()

    user_row = {
        "user_id": context.user_data.get("user_id"),
        "username": context.user_data.get("username"),
        "full_name_telegram": context.user_data.get("full_name_telegram"),
        "role": ROLE_EXPERT,
        "city": "",
        "email": "",
        "referrer": context.user_data.get("referrer", ""),
        "joined_via_expert_id": context.user_data.get("joined_via_expert_id", ""),
        "created_at": context.user_data.get("created_at"),
    }

    expert_row = {
        "user_id": context.user_data.get("user_id"),
        "expert_full_name": context.user_data.get("expert_full_name"),
        "expert_field": context.user_data.get("expert_field"),
        "expert_experience": context.user_data.get("expert_experience"),
        "expert_position": context.user_data.get("expert_position"),
        "expert_links": context.user_data.get("expert_links"),
        "expert_why": context.user_data.get("expert_why"),
        "created_at": context.user_data.get("created_at"),
        "group_link": "",
        "status": "pending",
        "supporters_count": 0,
    }

    sheets_service.append_user_row(user_row)
    sheets_service.append_expert_row(expert_row)

    await log(context, "Expert application submitted", user=update.effective_user, extra=expert_row)

    if LOG_GROUP_ID:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("אישור", callback_data=f"expert_approve:{expert_row['user_id']}"),
                InlineKeyboardButton("דחייה", callback_data=f"expert_reject:{expert_row['user_id']}"),
            ]
        ])

        text = (
            "מומחה חדש ממתין לאישור:\n"
            f"שם: {expert_row['expert_full_name']}\n"
            f"תחום: {expert_row['expert_field']}\n"
            f"מקום: {expert_row['expert_position']}\n"
            f"user_id: {expert_row['user_id']}\n"
        )

        await context.bot.send_message(
            chat_id=int(LOG_GROUP_ID),
            text=text,
            reply_markup=keyboard,
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 פתיחת תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
        [InlineKeyboardButton("ℹ️ לראות את פאנל המומחה שלי", callback_data=CALLBACK_MENU_EXPERT)],
    ])

    await update.message.reply_text(
        "תודה! בקשה לאישור נשלחה.\n"
        "נעדכן אותך כאן ברגע שהבקשה תאושר או תידחה.\n\n"
        "בינתיים, מה תרצה לעשות?",
        reply_markup=keyboard,
    )
    return ConversationHandler.END

# ===============================
# תמיכה במומחה (callback)
# ===============================

async def handle_support_expert_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    מטפל בלחיצה על 'תמיכה במומחה זה' מתוך פרופיל מומחה.
    מניע עדכון supporters_count בגיליון ומונע תמיכה כפולה על ידי אותו משתמש.
    """
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    if not data or not data.startswith("support_expert:"):
        await query.message.reply_text("בקשה לא תקינה.")
        return

    _, expert_id = data.split(":", 1)
    # בדיקה אם המומחה קיים ומאושר
    expert = sheets_service.get_expert_by_id(expert_id)
    if not expert:
        await query.message.reply_text("מומחה לא נמצא.")
        return

    if expert.get("status") != "approved":
        await query.message.reply_text("לא ניתן לתמוך במומחה שאינו מאושר.")
        return

    # מניעת תמיכה כפולה: נבדוק בגיליון Users אם המשתמש כבר רשום כתומך עם joined_via_expert_id זה
    supporter = sheets_service.get_supporter_by_id(str(user.id))
    if supporter:
        # אם כבר רשום ותומך במומחה זה — נמנע
        joined = str(supporter.get("joined_via_expert_id", "") or "")
        if joined == str(expert_id):
            await query.message.reply_text("כבר תמכת במומחה זה. תודה רבה!")
            return
        # אחרת נעדכן את השורה של המשתמש עם joined_via_expert_id ונגדיל מונה
        supporter_row = supporter
        supporter_row["joined_via_expert_id"] = str(expert_id)
        # נעדכן את השורה בגיליון על ידי הוספת שורה חדשה (append) או עדכון ישיר — כאן נשתמש ב־append_user_row לשמירה עקבית
        sheets_service.append_user_row(supporter_row)
    else:
        # המשתמש לא קיים — נרשום אותו כתומך מינימלי עם joined_via_expert_id
        new_user = {
            "user_id": str(user.id),
            "username": user.username or "",
            "full_name_telegram": user.full_name or "",
            "role": "supporter",
            "city": "",
            "email": "",
            "referrer": "",
            "joined_via_expert_id": str(expert_id),
            "created_at": datetime.utcnow().isoformat(),
            "supporter_feedback": "",
            "phone": "",
        }
        sheets_service.append_user_row(new_user)

    # הגדלת מונה תומכים של המומחה
    sheets_service.increment_expert_supporters(str(expert_id))

    await query.message.reply_text("תודה על התמיכה! מספר התומכים עודכן.")
