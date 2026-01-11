# bot/handlers/expert_handlers.py
# ==================================
# תהליך הרשמת מומחה + תמיכה במומחה + אישור/דחייה + ניקוד
# ==================================

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from services.sheets_service import sheets_service
from services.logger_service import log
from services.level_service import level_service
from bot.core.session_manager import session_manager
from utils.constants import EXPERTS_GROUP_ID, LOG_GROUP_ID


def build_expert_referral_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start=expert_{user_id}"


# ===============================
# שלבי הרשמת מומחה
# ===============================

async def expert_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = update.message.text.strip()

    session = session_manager.get_or_create(user)
    session.metadata["expert_name"] = name

    await update.message.reply_text("מה תחום המומחיות שלך?")
    return


async def expert_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    field = update.message.text.strip()

    session = session_manager.get_or_create(user)
    session.metadata["expert_field"] = field

    await update.message.reply_text("ספר בקצרה על הניסיון שלך:")
    return


async def expert_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    exp = update.message.text.strip()

    session = session_manager.get_or_create(user)
    session.metadata["expert_experience"] = exp

    await update.message.reply_text("איזה מקום תרצה לבחור (1–120)?")
    return


async def expert_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pos = update.message.text.strip()

    session = session_manager.get_or_create(user)
    session.metadata["expert_position"] = pos

    await update.message.reply_text("יש לך קישורים מקצועיים? (LinkedIn, אתר, מאמרים)")
    return


async def expert_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    links = update.message.text.strip()

    session = session_manager.get_or_create(user)
    session.metadata["expert_links"] = links

    await update.message.reply_text("למה אתה רוצה להיות מומחה בתנועה?")
    return


async def expert_why(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    why = update.message.text.strip()

    session = session_manager.get_or_create(user)
    session.metadata["expert_why"] = why

    record = {
        "user_id": user.id,
        "expert_full_name": session.metadata.get("expert_name", user.full_name),
        "expert_field": session.metadata.get("expert_field", ""),
        "expert_experience": session.metadata.get("expert_experience", ""),
        "expert_position": session.metadata.get("expert_position", ""),
        "expert_links": session.metadata.get("expert_links", ""),
        "expert_why": session.metadata.get("expert_why", ""),
        "created_at": session.created_at,
        "status": "pending",
        "group_link": "",
        "supporters_count": 0,
    }

    sheets_service.append_expert(record)

    # ניקוד: בקשת מומחה
    try:
        level_service.add_points(user.id, "expert", 10)
    except Exception:
        pass

    await log(context, "Expert application submitted", user=user, extra=record)

    # שליחה לקבוצת מומחים/לוג
    if EXPERTS_GROUP_ID:
        try:
            await context.bot.send_message(
                chat_id=int(EXPERTS_GROUP_ID),
                text=(
                    "🧠 בקשת מומחה חדשה:\n\n"
                    f"שם: {record['expert_full_name']}\n"
                    f"תחום: {record['expert_field']}\n"
                    f"ניסיון: {record['expert_experience']}\n"
                    f"מקום: {record['expert_position']}\n"
                    f"user_id: {user.id}"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✔ לאשר", callback_data=f"expert_approve:{user.id}"),
                        InlineKeyboardButton("❌ לדחות", callback_data=f"expert_reject:{user.id}"),
                    ]
                ]),
            )
        except Exception:
            pass

    if LOG_GROUP_ID:
        try:
            await context.bot.send_message(
                chat_id=int(LOG_GROUP_ID),
                text=f"[LOG] בקשת מומחה חדשה מ־{user.full_name} (id={user.id})",
            )
        except Exception:
            pass

    await update.message.reply_text(
        "הבקשה שלך נשלחה! 🎉\n"
        "אדמין יעבור עליה ויאשר/ידחה בהקדם."
    )
    return


# ===============================
# תמיכה במומחה
# ===============================

async def handle_support_expert_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    _, expert_id = query.data.split(":", 1)
    sheets_service.increment_expert_supporters(expert_id, step=1)

    # ניקוד: תמיכה במומחה (לתומך)
    try:
        level_service.add_points(user.id, "supporter", 2)
    except Exception:
        pass

    await query.message.reply_text("תודה על התמיכה! 🙌")


# ===============================
# אישור / דחייה של מומחה
# ===============================

async def expert_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    action, user_id = data.split(":", 1)

    if action == "expert_approve":
        sheets_service.update_expert_status(user_id, "approved")
        # ניקוד: מומחה אושר
        try:
            level_service.add_points(int(user_id), "expert", 20)
        except Exception:
            pass
        await query.message.reply_text("✔ המומחה אושר!")
    else:
        sheets_service.update_expert_status(user_id, "rejected")
        await query.message.reply_text("❌ המומחה נדחה.")
