# bot/handlers/bot_handlers.py
# ===============================
# נקודת ריכוז לפקודות כלליות, תפריטים ו־ConversationHandler
# ===============================

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot.flows import start_flow, menu_flow
from bot.handlers.supporter_handlers import (
    supporter_name,
    supporter_city,
    supporter_email,
    supporter_phone,
    supporter_feedback,
)
from bot.handlers.expert_handlers import (
    expert_name,
    expert_field,
    expert_experience,
    expert_position,
    expert_links,
    expert_why,
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
from bot.core.locale_service import locale_service
from bot.core.session_manager import session_manager
from services.logger_service import log
from services.sheets_service import sheets_service
from services.level_service import level_service
from utils.constants import ROLE_SUPPORTER


# ===============================
# /start – מעביר ל־start_flow
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    start_param = ""
    if " " in text:
        # /start xyz
        _, start_param = text.split(" ", 1)
    session_manager.get_or_create(user, start_param=start_param)
    # נשמור את start_param לתהליך תומך אם יתבצע
    context.user_data["start_param"] = start_param
    await start_flow.handle_start(update, context)


# ===============================
# /menu – מעביר ל־menu_flow
# ===============================

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_flow.handle_menu_command(update, context)


# ===============================
# /all – תפריט על בסיסי (בשלב ראשון)
# ===============================

async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    תפריט ALL בסיסי – בשלב זה רק מסביר מה קיים ונותן פקודות שימושיות.
    אפשר להרחיב אותו בהמשך למקלדת אינטראקטיבית.
    """
    user = update.effective_user
    await log(context, "ALL command", user=user)

    text = (
        "📋 מרכז שליטה /ALL\n\n"
        "פקודות שימושיות:\n"
        "/menu – תפריט ראשי\n"
        "/level – הרמה והנקודות שלך\n"
        "/supporter_panel – פאנל תומך\n"
        "/expert_panel – פאנל מומחה (אם הגשת מועמדות)\n"
        "/leaderboard – טבלת מובילים\n"
        "/positions – רשימת מקומות (admin)\n"
    )
    await update.message.reply_text(text)


# ===============================
# /help – רשימת פקודות
# ===============================

async def all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 רשימת פקודות:\n\n"
        "/start – התחלה\n"
        "/menu – תפריט ראשי\n"
        "/all – מרכז שליטה\n"
        "/level – הרמה והנקודות שלך\n"
        "/supporter_panel – פאנל תומך\n"
        "/expert_panel – פאנל מומחה\n"
        "/leaderboard – טבלת מובילים\n"
        "/myid – הצגת user_id\n"
        "/groupid – הצגת group_id (בקבוצה)\n"
        "/positions – רשימת מקומות (admin)\n"
        "/help – עזרה\n"
    )
    await update.message.reply_text(text)


# ===============================
# /myid, /groupid
# ===============================

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"user_id שלך: {update.effective_user.id}")


async def group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ("group", "supergroup"):
        await update.message.reply_text(f"group_id: {chat.id}")
    else:
        await update.message.reply_text("יש להריץ את הפקודה בתוך קבוצה.")


# ===============================
# /level – תצוגת רמות ונקודות
# ===============================

async def level_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log(context, "Level command", user=user)

    # ננסה לבדוק האם קיים כתומך/מומחה
    supporter = sheets_service.get_supporter_by_id(str(user.id))
    expert = sheets_service.get_expert_by_id(str(user.id))

    lines = []

    if supporter:
        points = level_service.get_points(user.id, "supporter")
        level_num = level_service.get_level(user.id, "supporter")
        level_name = level_service.get_level_name(user.id, "supporter")
        next_info = level_service.get_next_level_info(user.id, "supporter")
        lines.append("🧑‍🎓 פרופיל תומך:")
        lines.append(f"נקודות: {points}")
        lines.append(f"רמה: {level_num} – {level_name}")
        if next_info:
            lines.append(
                f"חסרות לך עוד {next_info['missing_points']} נקודות לרמה {next_info['next_level']} – {next_info['next_name']}"
            )
        lines.append("")

    if expert:
        points_e = level_service.get_points(user.id, "expert")
        level_num_e = level_service.get_level(user.id, "expert")
        level_name_e = level_service.get_level_name(user.id, "expert")
        next_info_e = level_service.get_next_level_info(user.id, "expert")
        lines.append("🧠 פרופיל מומחה:")
        lines.append(f"נקודות: {points_e}")
        lines.append(f"רמה: {level_num_e} – {level_name_e}")
        if next_info_e:
            lines.append(
                f"חסרות לך עוד {next_info_e['missing_points']} נקודות לרמה {next_info_e['next_level']} – {next_info_e['next_name']}"
            )
        lines.append("")

    if not supporter and not expert:
        lines.append("עדיין לא נרשמת כתומך או מומחה.\n")
        lines.append("התחל עם /start או /menu כדי להצטרף.")

    await update.message.reply_text("\n".join(lines))


# ===============================
# /supporter_panel – פאנל תומך בסיסי
# ===============================

async def supporter_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    supporter = sheets_service.get_supporter_by_id(str(user.id))

    if not supporter:
        await update.message.reply_text(
            "עדיין לא נרשמת כתומך.\nהשתמש ב־/menu ובחר 'תומך' כדי להירשם."
        )
        return

    points = level_service.get_points(user.id, "supporter")
    level_num = level_service.get_level(user.id, "supporter")
    level_name = level_service.get_level_name(user.id, "supporter")

    personal_link = f"https://t.me/{context.bot.username}?start={user.id}"

    text = (
        "📊 פאנל תומך:\n\n"
        f"שם: {supporter.get('full_name_telegram', user.full_name)}\n"
        f"עיר: {supporter.get('city', 'לא צויין')}\n"
        f"אימייל: {supporter.get('email', 'לא צויין')}\n\n"
        f"רמה: {level_num} – {level_name}\n"
        f"נקודות: {points}\n\n"
        "הקישור האישי שלך לשיתוף:\n"
        f"{personal_link}\n"
    )

    await update.message.reply_text(text)


# ===============================
# /expert_panel – פאנל מומחה בסיסי
# ===============================

async def expert_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    expert = sheets_service.get_expert_by_id(str(user.id))

    if not expert:
        await update.message.reply_text(
            "עדיין לא הגשת מועמדות כמומחה.\n"
            "השתמש ב־/menu ובחר 'מומחה' כדי להתחיל."
        )
        return

    points = level_service.get_points(user.id, "expert")
    level_num = level_service.get_level(user.id, "expert")
    level_name = level_service.get_level_name(user.id, "expert")

    status = expert.get("status", "pending")
    position = expert.get("expert_position", "לא נבחר")
    supporters_count = expert.get("supporters_count", 0)
    links = expert.get("expert_links", "")
    field = expert.get("expert_field", "")
    exp = expert.get("expert_experience", "")

    text = (
        "🧠 פאנל מומחה:\n\n"
        f"שם: {expert.get('expert_full_name', user.full_name)}\n"
        f"תחום: {field}\n"
        f"ניסיון: {exp}\n"
        f"מקום: {position}\n"
        f"סטטוס: {status}\n\n"
        f"רמה: {level_num} – {level_name}\n"
        f"נקודות: {points}\n"
        f"תומכים: {supporters_count}\n"
    )

    if links:
        text += f"\nקישורים מקצועיים:\n{links}\n"

    await update.message.reply_text(text)


# ===============================
# Callback menu router
# ===============================

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu_flow.handle_menu_callback(update, context)


# ===============================
# ConversationHandler הראשי
# ===============================

def get_conversation_handler() -> ConversationHandler:
    """
    ConversationHandler שמנהל את תהליכי התומך והמומחה.
    """
    return ConversationHandler(
        entry_points=[],
        states={
            SUPPORTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_name)],
            SUPPORTER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_city)],
            SUPPORTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_email)],
            SUPPORTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_phone)],
            SUPPORTER_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_feedback)],
            EXPERT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_name)],
            EXPERT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_field)],
            EXPERT_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_experience)],
            EXPERT_POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_position)],
            EXPERT_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_links)],
            EXPERT_WHY: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_why)],
        },
        fallbacks=[],
        name="main_conversation",
        persistent=False,
    )


# ===============================
# פקודה לא מוכרת
# ===============================

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = locale_service.detect_language(update.effective_user.language_code)
    await update.message.reply_text(locale_service.t("unknown_command", lang))
