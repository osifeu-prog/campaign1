import os
from datetime import datetime
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
import sheets_service

# ------------------ ENV / CONFIG ------------------

LOG_GROUP_ID = os.getenv("LOG_GROUP_ID", "")
ADMIN_IDS = [i for i in os.getenv("ADMIN_IDS", "").split(",") if i]

ALL_MEMBERS_GROUP_ID = os.getenv("ALL_MEMBERS_GROUP_ID", "")
ACTIVISTS_GROUP_ID = os.getenv("ACTIVISTS_GROUP_ID", "")
EXPERTS_GROUP_ID = os.getenv("EXPERTS_GROUP_ID", "")
SUPPORT_GROUP_ID = os.getenv("SUPPORT_GROUP_ID", "")

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


# ------------------ START ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text.startswith("/start "):
        parts = update.message.text.split(" ", maxsplit=1)
        if len(parts) == 2:
            context.user_data["referrer"] = parts[1]

    intro_text = (
        "ברוך הבא למערכת הרישום.\n\n"
        "TODO: הכנס כאן טקסט פתיחה משלך.\n\n"
        "איך תרצה להצטרף?"
    )

    keyboard = [
        [
            InlineKeyboardButton("מומחה", callback_data=ROLE_EXPERT),
            InlineKeyboardButton("תומך", callback_data=ROLE_SUPPORTER),
        ]
    ]

    if update.message:
        await update.message.reply_text(intro_text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(intro_text, reply_markup=InlineKeyboardMarkup(keyboard))

    return CHOOSING_ROLE


async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    role = query.data
    context.user_data["role"] = role
    context.user_data["user_id"] = query.from_user.id
    context.user_data["username"] = query.from_user.username
    context.user_data["full_name_telegram"] = query.from_user.full_name
    context.user_data["created_at"] = datetime.utcnow().isoformat()

    if role == ROLE_SUPPORTER:
        await query.edit_message_text("מה שמך המלא?")
        return SUPPORTER_NAME

    if role == ROLE_EXPERT:
        await query.edit_message_text("מה שמך המלא?")
        return EXPERT_NAME


# ------------------ SUPPORTER FLOW ------------------

async def supporter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_full_name"] = update.message.text.strip()
    await update.message.reply_text("באיזו עיר אתה גר?")
    return SUPPORTER_CITY


async def supporter_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_city"] = update.message.text.strip()
    await update.message.reply_text("כתובת אימייל (אפשר 'דלג'):")
    return SUPPORTER_EMAIL


async def supporter_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["supporter_email"] = "" if text.lower() in ["דלג", "skip"] else text

    user_row = {
        "user_id": context.user_data.get("user_id"),
        "username": context.user_data.get("username"),
        "full_name_telegram": context.user_data.get("full_name_telegram"),
        "role": ROLE_SUPPORTER,
        "city": context.user_data.get("supporter_city"),
        "email": context.user_data.get("supporter_email"),
        "referrer": context.user_data.get("referrer", ""),
        "created_at": context.user_data.get("created_at"),
    }

    sheets_service.append_user_row(user_row)

    await update.message.reply_text(
        "תודה שנרשמת כתומך.\n"
        f"https://t.me/{context.bot.username}?start={context.user_data['user_id']}"
    )

    return ConversationHandler.END


# ------------------ EXPERT FLOW ------------------

async def expert_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_full_name"] = update.message.text.strip()
    await update.message.reply_text("מה תחום המומחיות שלך?")
    return EXPERT_FIELD


async def expert_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_field"] = update.message.text.strip()
    await update.message.reply_text("ספר בקצרה על הניסיון שלך:")
    return EXPERT_EXPERIENCE


async def expert_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_experience"] = update.message.text.strip()
    await update.message.reply_text("על איזה מספר מקום מתוך 121 תרצה להתמודד?")
    return EXPERT_POSITION


async def expert_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("נא להכניס מספר בין 1 ל-121.")
        return EXPERT_POSITION

    pos_num = int(text)
    if not (1 <= pos_num <= 121):
        await update.message.reply_text("נא לבחור מספר מקום בין 1 ל-121.")
        return EXPERT_POSITION

    if not sheets_service.position_is_free(str(pos_num)):
        await update.message.reply_text("המקום שבחרת תפוס. בחר אחר.")
        return EXPERT_POSITION

    context.user_data["expert_position"] = str(pos_num)

    sheets_service.assign_position(
        position_id=str(pos_num),
        user_id=str(context.user_data.get("user_id")),
        timestamp=context.user_data.get("created_at"),
    )

    await update.message.reply_text("המקום נרשם עבורך.\nהוסף קישורים:")
    return EXPERT_LINKS


async def expert_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_links"] = update.message.text.strip()
    await update.message.reply_text("כתוב כמה משפטים עליך:")
    return EXPERT_WHY


async def expert_why(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_why"] = update.message.text.strip()

    user_row = {
        "user_id": context.user_data.get("user_id"),
        "username": context.user_data.get("username"),
        "full_name_telegram": context.user_data.get("full_name_telegram"),
        "role": ROLE_EXPERT,
        "city": "",
        "email": "",
        "referrer": context.user_data.get("referrer", ""),
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
    }

    sheets_service.append_user_row(user_row)
    sheets_service.append_expert_row(expert_row)

    if LOG_GROUP_ID:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ אשר", callback_data=f"expert_approve:{expert_row['user_id']}"),
                InlineKeyboardButton("❌ דחה", callback_data=f"expert_reject:{expert_row['user_id']}"),
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

    await update.message.reply_text("תודה! בקשה לאישור נשלחה.")
    return ConversationHandler.END


# ------------------ ADMIN CALLBACKS ------------------

async def expert_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if str(query.from_user.id) not in ADMIN_IDS:
        await query.edit_message_text("אין לך הרשאה.")
        return

    action, user_id = query.data.split(":")

    if action == "expert_approve":
        sheets_service.update_expert_status(user_id, "approved")
        await _notify_expert(context, user_id, True)
        await query.edit_message_text("אושר.")
    else:
        sheets_service.update_expert_status(user_id, "rejected")
        await _notify_expert(context, user_id, False)
        await query.edit_message_text("נדחה.")


async def _notify_expert(context: ContextTypes.DEFAULT_TYPE, user_id: str, approved: bool):
    text = "המועמדות שלך אושרה." if approved else "המועמדות שלך נדחתה."
    await context.bot.send_message(chat_id=int(user_id), text=text)


# ------------------ POSITIONS COMMANDS ------------------

async def list_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    positions = sheets_service.get_positions()
    text = "📌 רשימת המקומות:\n\n"
    for pos in positions:
        status = "🟢 תפוס" if pos["expert_user_id"] else "⚪ פנוי"
        text += f"{pos['position_id']}. {pos['title']} — {status}\n"
    await update.message.reply_text(text)


async def position_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("שימוש: /position <מספר>")
        return

    pos = sheets_service.get_position(args[1])
    if not pos:
        await update.message.reply_text("מקום לא נמצא.")
        return

    text = (
        f"📌 מקום {pos['position_id']}\n"
        f"שם: {pos['title']}\n"
        f"תיאור: {pos['description']}\n"
        f"מומחה: {pos['expert_user_id'] or 'אין'}\n"
    )
    await update.message.reply_text(text)


async def assign_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) not in ADMIN_IDS:
        await update.message.reply_text("אין לך הרשאה.")
        return

    args = update.message.text.split()
    if len(args) < 3:
        await update.message.reply_text("שימוש: /assign <מקום> <user_id>")
        return

    sheets_service.assign_position(args[1], args[2], datetime.utcnow().isoformat())
    await update.message.reply_text("בוצע.")


# ------------------ SUPPORT / ID HELPERS ------------------

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Your ID:\n`{update.effective_user.id}`",
        parse_mode="Markdown",
    )


async def group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Group ID:\n`{update.effective_chat.id}`",
        parse_mode="Markdown",
    )


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /support <טקסט חופשי>
    שולח את הפנייה לקבוצת התמיכה (SUPPORT_GROUP_ID), אם מוגדרת.
    """
    if not SUPPORT_GROUP_ID:
        await update.message.reply_text("קבוצת התמיכה לא מוגדרת במערכת.")
        return

    text = update.message.text.replace("/support", "", 1).strip()
    if not text:
        await update.message.reply_text("כתוב את הפנייה שלך אחרי /support")
        return

    user = update.effective_user
    await context.bot.send_message(
        chat_id=int(SUPPORT_GROUP_ID),
        text=(
            "פנייה חדשה מהבוט:\n"
            f"User ID: {user.id}\n"
            f"Username: @{user.username if user.username else 'ללא'}\n"
            f"שם: {user.full_name}\n\n"
            f"תוכן הפנייה:\n{text}"
        ),
    )

    await update.message.reply_text("הפנייה נשלחה. תודה.")


async def all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📌 פקודות זמינות:\n\n"
        "/start – התחלת רישום\n"
        "/myid – הצגת ה־ID שלך\n"
        "/groupid – הצגת ה־ID של הקבוצה\n"
        "/positions – רשימת מקומות\n"
        "/position <מספר> – פרטי מקום\n"
        "/assign <מקום> <user_id> – שיוך מקום (אדמין)\n"
        "/support <טקסט> – שליחת פנייה לצוות התמיכה\n"
        "/ALL – רשימת כל הפקודות\n"
    )
    await update.message.reply_text(text)


# ------------------ CANCEL + CONVERSATION ------------------

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ההרשמה בוטלה.")
    return ConversationHandler.END


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ROLE: [
                CallbackQueryHandler(choose_role, pattern="^(supporter|expert)$")
            ],
            SUPPORTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_name)
            ],
            SUPPORTER_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_city)
            ],
            SUPPORTER_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_email)
            ],
            EXPERT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_name)
            ],
            EXPERT_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_field)
            ],
            EXPERT_EXPERIENCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_experience)
            ],
            EXPERT_POSITION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_position)
            ],
            EXPERT_LINKS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_links)
            ],
            EXPERT_WHY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_why)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )
