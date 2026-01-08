import os
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

# Optional: environment values for admin/log groups (used later)
LOG_GROUP_ID = os.getenv("LOG_GROUP_ID", "")
ADMIN_IDS = [i for i in os.getenv("ADMIN_IDS", "").split(",") if i]

# Conversation states
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
    """
    Entry point for /start.
    Shows introduction and asks user how they want to join.
    """

    # Handle referral: /start <referrer_id>
    if update.message and update.message.text.startswith("/start "):
        parts = update.message.text.split(" ", maxsplit=1)
        if len(parts) == 2:
            context.user_data["referrer"] = parts[1]

    # TODO: החלף את הטקסט הזה בטקסט הפתיחה שלך על התנועה, החזון, 121 המקומות וכו'.
    intro_text = (
        "ברוך הבא למערכת הרישום של התנועה.\n\n"
        "כאן ניתן להירשם כתומך או כמומחה, בצורה שקופה ומסודרת.\n"
        "המערכת שומרת את הנתונים באופן גלוי, כך שניתן להבין מי משתתף ועל מה הוא מתמודד.\n\n"
        "איך תרצה להצטרף?"
    )

    keyboard = [
        [
            InlineKeyboardButton("מומחה", callback_data=ROLE_EXPERT),
            InlineKeyboardButton("תומך", callback_data=ROLE_SUPPORTER),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(intro_text, reply_markup=reply_markup)
    else:
        # במקרה של callback (נדיר עבור /start, אבל משאיר ליציבות)
        await update.callback_query.message.reply_text(intro_text, reply_markup=reply_markup)

    return CHOOSING_ROLE


async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chooses either 'expert' or 'supporter' via inline button."""
    query = update.callback_query
    await query.answer()

    role = query.data
    context.user_data["role"] = role
    context.user_data["user_id"] = query.from_user.id
    context.user_data["username"] = query.from_user.username
    context.user_data["full_name_telegram"] = query.from_user.full_name

    if role == ROLE_SUPPORTER:
        await query.edit_message_text("מצוין. נתחיל ברישום כתומך.\nמה שמך המלא?")
        return SUPPORTER_NAME

    if role == ROLE_EXPERT:
        await query.edit_message_text("מעולה. נתחיל ברישום כמומחה.\nמה שמך המלא?")
        return EXPERT_NAME


# ---------- SUPPORTER FLOW ----------

async def supporter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_full_name"] = update.message.text.strip()
    await update.message.reply_text("באיזו עיר אתה גר?")
    return SUPPORTER_CITY


async def supporter_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_city"] = update.message.text.strip()
    await update.message.reply_text("כתובת אימייל (אפשר לכתוב 'דלג' אם אינך רוצה למסור):")
    return SUPPORTER_EMAIL


async def supporter_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower() in ["דלג", "skip"]:
        context.user_data["supporter_email"] = ""
    else:
        context.user_data["supporter_email"] = text

    # כאן אפשר לחבר ל-sheets_service בעתיד
    # TODO: חיבור לשמירה בגיליון Users (append_user_row)
    print("SUPPORTER DATA:", context.user_data)

    # אפשר להכניס כאן טקסט יותר מפורט על התנועה, הצמיחה דרך שיתוף וכו'
    # TODO: עדכן את הטקסט בהתאם למסרים שלך.
    await update.message.reply_text(
        "תודה שנרשמת כתומך.\n"
        "הרישום שלך נשמר במערכת.\n"
        "תוכל לשתף את הקישור לבוט עם חברים שירצו להצטרף:\n"
        f"https://t.me/{context.bot.username}?start={context.user_data['user_id']}"
    )

    return ConversationHandler.END


# ---------- EXPERT FLOW ----------

async def expert_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_full_name"] = update.message.text.strip()
    await update.message.reply_text("מה תחום המומחיות המרכזי שלך?")
    return EXPERT_FIELD


async def expert_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_field"] = update.message.text.strip()
    await update.message.reply_text("ספר בקצרה על הניסיון שלך בתחום (כמה משפטים):")
    return EXPERT_EXPERIENCE


async def expert_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_experience"] = update.message.text.strip()
    await update.message.reply_text("על איזה מספר מקום מתוך 121 תרצה להתמודד?")
    return EXPERT_POSITION


async def expert_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_position"] = update.message.text.strip()
    await update.message.reply_text(
        "הוסף קישורים רלוונטיים (אתר, רשתות חברתיות, מאמרים, וידאו וכדומה):"
    )
    return EXPERT_LINKS


async def expert_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_links"] = update.message.text.strip()
    await update.message.reply_text(
        "לסיום, כתוב כמה משפטים שמסבירים למה אתה מתאים לתפקיד ולתחום שבחרת:"
    )
    return EXPERT_WHY


async def expert_why(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_why"] = update.message.text.strip()

    # TODO: כאן תחבר ל-sheets_service לשמירת מומחה בגיליון Experts (append_expert_row)
    print("EXPERT DATA:", context.user_data)

    # שליחת לוג לקבוצת לוגים, אם קיימת
    if LOG_GROUP_ID:
        try:
            await context.bot.send_message(
                chat_id=int(LOG_GROUP_ID),
                text=f"מומחה חדש נרשם:\n{context.user_data}",
            )
        except Exception as e:
            print("Failed to send log message:", e)

    # TODO: כאן אפשר להכניס טקסט על תהליך האישור, על צפייה בחומרים, בחירה במומחים וכו'.
    await update.message.reply_text(
        "תודה שנרשמת כמומחה.\n"
        "הפרטים שלך נשמרו במערכת.\n"
        "בהמשך יוכלו לראות את החומרים שסיפקת ולהעריך את התאמתך."
    )

    return ConversationHandler.END


# ---------- CANCEL ----------

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ההרשמה בוטלה. אפשר תמיד להתחיל מחדש עם /start.")
    return ConversationHandler.END


def get_conversation_handler() -> ConversationHandler:
    """
    Returns the ConversationHandler to be registered in main.py.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ROLE: [CallbackQueryHandler(choose_role)],
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
