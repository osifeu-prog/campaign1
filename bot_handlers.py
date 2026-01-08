from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
)
import os

# ENV
LOG_GROUP_ID = os.getenv("LOG_GROUP_ID")
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

# States
(
    CHOOSING_ROLE,
    SUPPORTER_NAME,
    SUPPORTER_CITY,
    SUPPORTER_EMAIL,
    EXPERT_NAME,
    EXPERT_FIELD,
    EXPERT_EXPERIENCE,
    EXPERT_POSITION,
    EXPERT_LINKS,
    EXPERT_WHY,
) = range(10)

ROLE_SUPPORTER = "supporter"
ROLE_EXPERT = "expert"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Opening message + choose role"""

    # Referral
    if update.message and update.message.text.startswith("/start "):
        ref = update.message.text.split(" ")[1]
        context.user_data["referrer"] = ref

    text = (
        "🌟 *ברוך הבא לתנועת אחדות!* 🌟\n\n"
        "תנועה אזרחית שקמה בעקבות אירועי 7.10, במטרה להחליף את 120 חברי הכנסת "
        "ב־121 מומחים שנבחרים על ידי הציבור.\n\n"
        "המערכת הזו היא *קלפי דיגיטלית שקופה* — כמו חוזה חכם:\n"
        "• כל רישום גלוי\n"
        "• כל נתון שקוף\n"
        "• אין מניפולציות\n\n"
        "איך תרצה להצטרף?"
    )

    keyboard = [
        [
            InlineKeyboardButton("🧠 מומחה", callback_data=ROLE_EXPERT),
            InlineKeyboardButton("🤝 תומך", callback_data=ROLE_SUPPORTER),
        ]
    ]

    await update.message.reply_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

    return CHOOSING_ROLE


async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    role = query.data
    context.user_data["role"] = role
    context.user_data["user_id"] = query.from_user.id
    context.user_data["username"] = query.from_user.username
    context.user_data["full_name_telegram"] = query.from_user.full_name

    if role == ROLE_SUPPORTER:
        await query.edit_message_text("מצוין! מה שמך המלא?")
        return SUPPORTER_NAME

    if role == ROLE_EXPERT:
        await query.edit_message_text("מעולה! מה שמך המלא?")
        return EXPERT_NAME


# ---------- SUPPORTER FLOW ----------

async def supporter_name(update, context):
    context.user_data["supporter_full_name"] = update.message.text.strip()
    await update.message.reply_text("באיזו עיר אתה גר?")
    return SUPPORTER_CITY


async def supporter_city(update, context):
    context.user_data["supporter_city"] = update.message.text.strip()
    await update.message.reply_text("כתובת אימייל (אפשר 'דלג'):")
    return SUPPORTER_EMAIL


async def supporter_email(update, context):
    text = update.message.text.strip()
    context.user_data["supporter_email"] = "" if text.lower() in ["דלג", "skip"] else text

    # Log
    if LOG_GROUP_ID:
        await context.bot.send_message(
            chat_id=LOG_GROUP_ID,
            text=f"🟦 תומך חדש:\n{context.user_data}",
        )

    await update.message.reply_text(
        "תודה שנרשמת כתומך בתנועת אחדות!\n"
        "הרישום שלך שקוף וגלוי לציבור.\n"
        "תוכל לשתף את הבוט עם חברים:\n"
        f"https://t.me/{context.bot.username}?start={context.user_data['user_id']}"
    )

    return ConversationHandler.END


# ---------- EXPERT FLOW ----------

async def expert_name(update, context):
    context.user_data["expert_full_name"] = update.message.text.strip()
    await update.message.reply_text("מה תחום המומחיות המרכזי שלך?")
    return EXPERT_FIELD


async def expert_field(update, context):
    context.user_data["expert_field"] = update.message.text.strip()
    await update.message.reply_text("ספר בקצרה על הניסיון שלך:")
    return EXPERT_EXPERIENCE


async def expert_experience(update, context):
    context.user_data["expert_experience"] = update.message.text.strip()
    await update.message.reply_text("על איזה מספר מקום מתוך 121 תרצה להתמודד?")
    return EXPERT_POSITION


async def expert_position(update, context):
    context.user_data["expert_position"] = update.message.text.strip()
    await update.message.reply_text("הוסף קישורים לחומרים שלך (אתר, רשתות, מאמרים):")
    return EXPERT_LINKS


async def expert_links(update, context):
    context.user_data["expert_links"] = update.message.text.strip()
    await update.message.reply_text("למה אתה? כתוב 3–5 משפטים:")
    return EXPERT_WHY


async def expert_why(update, context):
    context.user_data["expert_why"] = update.message.text.strip()

    # Log to admin group
    if LOG_GROUP_ID:
        await context.bot.send_message(
            chat_id=LOG_GROUP_ID,
            text=f"🟥 מומחה חדש ממתין לאישור:\n{context.user_data}",
        )

    await update.message.reply_text(
        "תודה שנרשמת כמומחה בתנועת אחדות!\n"
        "הפרטים שלך נרשמו בצורה שקופה.\n"
        "אדמין יאשר אותך בקרוב."
    )

    return ConversationHandler.END


# ---------- CANCEL ----------

async def cancel(update, context):
    await update.message.reply_text("ההרשמה בוטלה.")
    return ConversationHandler.END


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ROLE: [CallbackQueryHandler(choose_role)],
            SUPPORTER_NAME: [MessageHandler(filters.TEXT, supporter_name)],
            SUPPORTER_CITY: [MessageHandler(filters.TEXT, supporter_city)],
            SUPPORTER_EMAIL: [MessageHandler(filters.TEXT, supporter_email)],
            EXPERT_NAME: [MessageHandler(filters.TEXT, expert_name)],
            EXPERT_FIELD: [MessageHandler(filters.TEXT, expert_field)],
            EXPERT_EXPERIENCE: [MessageHandler(filters.TEXT, expert_experience)],
            EXPERT_POSITION: [MessageHandler(filters.TEXT, expert_position)],
            EXPERT_LINKS: [MessageHandler(filters.TEXT, expert_links)],
            EXPERT_WHY: [MessageHandler(filters.TEXT, expert_why)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
