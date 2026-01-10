# bot/handlers/supporter_handlers.py
# ==================================
# תהליך הרשמת תומך – 5 שלבים מלאים
# ==================================

from telegram import Update
from telegram.ext import ContextTypes

from services.sheets_service import sheets_service
from services.logger_service import log
from bot.core.session_manager import session_manager
from utils.constants import SUPPORT_GROUP_ID


async def supporter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = update.message.text.strip()

    session = session_manager.get_or_create(user)
    session.metadata["supporter_name"] = name

    await log(context, "Supporter name received", user=user, extra={"name": name})
    await update.message.reply_text("באיזו עיר אתה גר?")
    

async def supporter_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    city = update.message.text.strip()

    session = session_manager.get_or_create(user)
    session.metadata["supporter_city"] = city

    await log(context, "Supporter city received", user=user, extra={"city": city})
    await update.message.reply_text("מה כתובת האימייל שלך?")
    

async def supporter_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    email = update.message.text.strip()

    session = session_manager.get_or_create(user)
    session.metadata["supporter_email"] = email

    await log(context, "Supporter email received", user=user, extra={"email": email})
    await update.message.reply_text("מה מספר הטלפון שלך?")
    

async def supporter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    phone = update.message.text.strip()

    session = session_manager.get_or_create(user)
    session.metadata["supporter_phone"] = phone

    await log(context, "Supporter phone received", user=user, extra={"phone": phone})
    await update.message.reply_text("רוצה להוסיף הערה או משוב? (לא חובה)")
    

async def supporter_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    feedback = update.message.text.strip()

    session = session_manager.get_or_create(user)
    session.metadata["supporter_feedback"] = feedback

    # שמירה לשיטס
    record = {
        "user_id": user.id,
        "username": user.username or "",
        "full_name_telegram": session.metadata.get("supporter_name", user.full_name),
        "role": "supporter",
        "city": session.metadata.get("supporter_city", ""),
        "email": session.metadata.get("supporter_email", ""),
        "phone": session.metadata.get("supporter_phone", ""),
        "referrer": session.last_deeplink or "",
        "joined_via_expert_id": "",
        "created_at": session.created_at,
    }

    sheets_service.append_user(record)

    await log(context, "Supporter registered", user=user, extra=record)

    # שליחה לקבוצת תומכים
    if SUPPORT_GROUP_ID:
        try:
            await context.bot.send_message(
                chat_id=int(SUPPORT_GROUP_ID),
                text=f"🎉 תומך חדש הצטרף!\n\nשם: {record['full_name_telegram']}\nעיר: {record['city']}\nאימייל: {record['email']}\nטלפון: {record['phone']}",
            )
        except Exception:
            pass

    await update.message.reply_text(
        "תודה שנרשמת כתומך! 🎉\n\n"
        "עכשיו אתה חלק מתנועת אחדות.\n"
        "תוכל לשתף את הקישור האישי שלך דרך התפריט הראשי."
    )
