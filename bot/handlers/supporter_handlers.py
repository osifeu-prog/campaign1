# bot/handlers/supporter_handlers.py
# ===============================
# תהליך הרשמת תומך מלא, מבוסס states
# ===============================

import re
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from bot.states import (
    SUPPORTER_NAME,
    SUPPORTER_CITY,
    SUPPORTER_EMAIL,
    SUPPORTER_PHONE,
    SUPPORTER_FEEDBACK,
)
from utils.constants import (
    ROLE_SUPPORTER, 
    CALLBACK_MENU_MAIN, 
    CALLBACK_APPLY_EXPERT,
    WHATSAPP_GROUP_LINK,
    POINTS_FOR_SUPPORTER_REGISTRATION
)
from services import sheets_service
from services.logger_service import log
from services.level_service import level_service


def build_personal_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start={user_id}"


async def supporter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_full_name"] = update.message.text.strip()
    await log(
        context,
        "Supporter name entered",
        user=update.effective_user,
        extra={"supporter_full_name": context.user_data["supporter_full_name"]},
    )
    await update.message.reply_text("באיזו עיר אתה גר?")
    return SUPPORTER_CITY


async def supporter_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_city"] = update.message.text.strip()
    await log(
        context,
        "Supporter city entered",
        user=update.effective_user,
        extra={"supporter_city": context.user_data["supporter_city"]},
    )
    await update.message.reply_text("כתובת אימייל (אפשר לכתוב 'דלג'):")
    return SUPPORTER_EMAIL


async def supporter_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.lower() not in ["דלג", "skip", ""]:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", text):
            await update.message.reply_text(
                "האימייל לא נראה תקין. דוגמה: name@example.com או כתוב 'דלג'."
            )
            return SUPPORTER_EMAIL
        context.user_data["supporter_email"] = text
    else:
        context.user_data["supporter_email"] = ""

    await log(
        context,
        "Supporter email entered",
        user=update.effective_user,
        extra={"supporter_email": context.user_data["supporter_email"]},
    )
    await update.message.reply_text("מה מספר הטלפון שלך? (אפשר 'דלג')")
    return SUPPORTER_PHONE


async def supporter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.lower() not in ["דלג", "skip", ""]:
        if not re.match(r"^[0-9+\-\s]{7,20}$", text):
            await update.message.reply_text(
                "מספר הטלפון לא נראה תקין. דוגמה: 0501234567 או כתוב 'דלג'."
            )
            return SUPPORTER_PHONE
        context.user_data["supporter_phone"] = text
    else:
        context.user_data["supporter_phone"] = ""

    await log(
        context,
        "Supporter phone entered",
        user=update.effective_user,
        extra={"supporter_phone": context.user_data["supporter_phone"]},
    )
    await update.message.reply_text("מה גרם לך להצטרף לתנועה? (כמה משפטים)")
    return SUPPORTER_FEEDBACK


async def supporter_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_feedback"] = update.message.text.strip()

    if "created_at" not in context.user_data:
        context.user_data["created_at"] = datetime.utcnow().isoformat()

    start_param = context.user_data.get("start_param", "")
    referrer = ""
    joined_via_expert_id = ""
    if start_param:
        if str(start_param).startswith("expert_"):
            joined_via_expert_id = str(start_param).split("_", 1)[1]
        else:
            referrer = str(start_param)

    user_row = {
        "user_id": context.user_data.get("user_id"),
        "username": context.user_data.get("username"),
        "full_name_telegram": context.user_data.get("full_name_telegram"),
        "role": ROLE_SUPPORTER,
        "city": context.user_data.get("supporter_city"),
        "email": context.user_data.get("supporter_email"),
        "referrer": referrer,
        "joined_via_expert_id": joined_via_expert_id,
        "created_at": context.user_data.get("created_at"),
        "feedback": context.user_data.get("supporter_feedback", ""),
        "phone": context.user_data.get("supporter_phone", ""),
        "whatsapp_link_sent": "FALSE",  # יסומן TRUE כשנשלח
        "points": POINTS_FOR_SUPPORTER_REGISTRATION,  # נקודות על רישום
        "level": 1,  # רמה התחלתית
        "last_activity": datetime.utcnow().isoformat(),
    }

    sheets_service.append_user(user_row)
    await log(context, "Supporter registered", user=update.effective_user, extra=user_row)

    # הוספת נקודות דרך level_service
    try:
        level_service.add_points(update.effective_user.id, "supporter", POINTS_FOR_SUPPORTER_REGISTRATION)
    except Exception as e:
        print(f"Error adding points: {e}")

    personal_link = build_personal_link(context.bot.username, context.user_data["user_id"])

    text = (
        "🎉 תודה שנרשמת כתומך!\n\n"
        "**מה קיבלת עכשיו?**\n"
        f"• {POINTS_FOR_SUPPORTER_REGISTRATION} נקודות התחלתיות\n"
        "• רמת 'משתמש חדש'\n"
        "• גישה לכל התכנים והעדכונים\n\n"
        "**הקישור האישי שלך לשיתוף:**\n"
        f"{personal_link}\n"
        "כל מי שיצטרף דרכך יופיע אצלך כדאטה בגיליון ויעזור לך להתקדם ברמות!\n\n"
    )

    # הוספת לינק וואטסאפ אם קיים
    whatsapp_section = ""
    keyboard_buttons = []
    
    if WHATSAPP_GROUP_LINK:
        whatsapp_section = (
            f"\n**קבוצת הוואטסאפ שלנו:**\n"
            f"{WHATSAPP_GROUP_LINK}\n"
            "הצטרפו כדי להיות חלק מהקהילה ולהישאר מעודכנים!\n\n"
        )
        # סמן שנשלח הלינק
        sheets_service.mark_whatsapp_sent(str(update.effective_user.id))
        keyboard_buttons.append([InlineKeyboardButton("📱 הצטרפות לקבוצת וואטסאפ", url=WHATSAPP_GROUP_LINK)])
    
    text += whatsapp_section
    text += "מה תרצה לעשות עכשיו?"

    keyboard_buttons.extend([
        [InlineKeyboardButton("📣 לשתף את הקישור האישי שלי", url=personal_link)],
        [InlineKeyboardButton("🧠 להגיש מועמדות כמומחה", callback_data=CALLBACK_APPLY_EXPERT)],
        [InlineKeyboardButton("📋 פתיחת תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ])

    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    await update.message.reply_text(text, reply_markup=keyboard)
    return ConversationHandler.END
