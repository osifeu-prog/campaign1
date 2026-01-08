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

LOG_GROUP_ID = os.getenv("LOG_GROUP_ID", "")
ADMIN_IDS = [i for i in os.getenv("ADMIN_IDS", "").split(",") if i]

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
        "TODO: הכנס כאן טקסט פתיחה משלך (על התנועה, החזון, המבנה וכו').\n\n"
        "איך תרצה להצטרף?"
    )

    keyboard = [
        [
            InlineKeyboardButton("מומחה", callback_data=ROLE_EXPERT),
            InlineKeyboardButton("תומך", callback_data=ROLE_SUPPORTER),
        ]
    ]

    await update.message.reply_text(intro_text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    await update.message.reply_text("כתובת אימייל (אפשר לכתוב 'דלג'):")
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
        "תוכל לשתף את הקישור:\n"
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

    # בדיקה אם המקום פנוי בגיליון
    if not sheets_service.position_is_free(str(pos_num)):
        await update.message.reply_text(
            "המקום שבחרת כבר תפוס.\n"
            "נא לבחור מספר מקום אחר בין 1 ל-121."
        )
        return EXPERT_POSITION

    # אם פנוי – נשמור ב-user_data ונעדכן את הגיליון
    context.user_data["expert_position"] = str(pos_num)

    try:
        sheets_service.assign_position(
            position_id=str(pos_num),
            user_id=str(context.user_data.get("user_id")),
            timestamp=context.user_data.get("created_at"),
        )
    except Exception as e:
        print("Error assigning position:", e)
        await update.message.reply_text(
            "אירעה שגיאה בשיוך המקום. נסה שוב או פנה למנהל."
        )
        return EXPERT_POSITION

    await update.message.reply_text("המקום נרשם עבורך בהצלחה.\nהוסף קישורים רלוונטיים:")
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

    # לוג לקבוצת לוגים אם קיים
    if LOG_GROUP_ID:
        try:
            await context.bot.send_message(
                chat_id=int(LOG_GROUP_ID),
                text=f"מומחה חדש נרשם:\n{expert_row}",
            )
        except Exception as e:
            print("Failed to send log message:", e)

    await update.message.reply_text("תודה, הפרטים נשמרו והמקום שויך לך.")
    return ConversationHandler.END


# ------------------ POSITIONS COMMANDS ------------------

async def list_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    positions = sheets_service.get_positions()

    if not positions:
        await update.message.reply_text("אין נתונים על מקומות כרגע.")
        return

    text = "📌 רשימת המקומות:\n\n"
    for pos in positions:
        assigned = "🟢 תפוס" if pos["expert_user_id"] else "⚪ פנוי"
        text += f"{pos['position_id']}. {pos['title']} — {assigned}\n"

    await update.message.reply_text(text)


async def position_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("שימוש: /position <מספר>")
        return

    pos_id = args[1]
    pos = sheets_service.get_position(pos_id)

    if not pos:
        await update.message.reply_text("מקום לא נמצא.")
        return

    text = (
        f"📌 מקום {pos['position_id']}\n"
        f"שם: {pos['title']}\n"
        f"תיאור: {pos['description']}\n"
        f"מומחה משויך: {pos['expert_user_id'] or 'אין'}\n"
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

    pos_id = args[1]
    user_id = args[2]

    sheets_service.assign_position(pos_id, user_id, datetime.utcnow().isoformat())
    await update.message.reply_text(f"מקום {pos_id} שויך למומחה {user_id}.")


# ------------------ GROUP ID ------------------

async def group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await update.message.reply_text(
        f"Group ID:\n`{chat.id}`",
        parse_mode="Markdown"
    )


# ------------------ CANCEL ------------------

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ההרשמה בוטלה.")
    return ConversationHandler.END


def get_conversation_handler():
    # כאן אני משאיר את ה-conversation פשוט – כל הפקודות הנוספות הן מחוץ ל-flow
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SUPPORTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_name)],
            SUPPORTER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_city)],
            SUPPORTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_email)],
            EXPERT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_name)],
            EXPERT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_field)],
            EXPERT_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_experience)],
            EXPERT_POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_position)],
            EXPERT_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_links)],
            EXPERT_WHY: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_why)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
