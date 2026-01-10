# bot/handlers/supporter_handlers.py
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from services import sheets_service

async def apply_supporter_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("מתחילים בהרשמת תומך. איך קוראים לך?")
    return "SUPPORTER_NAME"

async def supporter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["supporter_name"] = name
    await update.message.reply_text("באיזו עיר אתה גר?")
    return "SUPPORTER_CITY"

async def supporter_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    context.user_data["supporter_city"] = city
    await update.message.reply_text("כתובת אימייל (אפשר לכתוב 'דלג'):")
    return "SUPPORTER_EMAIL"

async def supporter_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if email.lower() != "דלג" and "@" not in email:
        await update.message.reply_text("האימייל לא נראה תקין. דוגמה: name@example.com או כתוב 'דלג'.")
        return "SUPPORTER_EMAIL"
    context.user_data["supporter_email"] = "" if email.lower() == "דלג" else email
    await update.message.reply_text("מה מספר הטלפון שלך? (אפשר 'דלג')")
    return "SUPPORTER_PHONE"

async def supporter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data["supporter_phone"] = "" if phone.lower() == "דלג" else phone
    await update.message.reply_text("מה גרם לך להצטרף לתנועה? (כמה משפטים)")
    return "SUPPORTER_REASON"

async def supporter_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Idempotency guard for conversation end
    try:
        update_id = getattr(update, "update_id", None)
        if update_id is not None:
            last = context.chat_data.get("last_handled_update_id")
            if last == update_id:
                return -1
            context.chat_data["last_handled_update_id"] = update_id
    except Exception:
        pass

    reason = update.message.text.strip()
    if len(reason) < 20:
        await update.message.reply_text("נשמח לכמה משפטים נוספים (לפחות 20 תווים).")
        return "SUPPORTER_REASON"

    user_row = {
        "user_id": update.message.from_user.id,
        "username": update.message.from_user.username or "",
        "full_name_telegram": f"{update.message.from_user.first_name} {getattr(update.message.from_user, 'last_name', '')}".strip(),
        "role": "supporter",
        "city": context.user_data.get("supporter_city", ""),
        "email": context.user_data.get("supporter_email", ""),
        "phone": context.user_data.get("supporter_phone", ""),
        "referrer": "",
        "joined_via_expert_id": "",
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        sheets_service.append_user(user_row)
        await update.message.reply_text("תודה! הרשמתך נקלטה בהצלחה.")
    except Exception as e:
        print("⚠ Failed to append supporter:", e)
        await update.message.reply_text("אירעה שגיאה פנימית בעיבוד הבקשה. אנא נסה שנית בעוד רגע.")
    return -1
