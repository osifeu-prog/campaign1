# ===============================
# Router ראשי: start, menu, callbacks, conv handler
# ===============================

from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from utils.constants import (
    ADMIN_IDS,
    LOG_GROUP_ID,
    ROLE_SUPPORTER,
    ROLE_EXPERT,
    CALLBACK_MENU_MAIN,
    CALLBACK_MENU_SUPPORT,
    CALLBACK_MENU_EXPERT,
    CALLBACK_MENU_ADMIN,
    CALLBACK_APPLY_EXPERT,
    CALLBACK_APPLY_SUPPORTER,
    CALLBACK_ADMIN_PENDING_EXPERTS,
    CALLBACK_ADMIN_GROUPS,
    CALLBACK_MENU_POSITIONS,
)
from bot.states import (
    CHOOSING_ROLE,
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
from bot.keyboards import (
    build_main_menu_for_user,
    build_start_keyboard,
    build_supporter_profile_keyboard,
    build_expert_panel_keyboard,
    build_admin_panel_keyboard,
)
from bot.supporter_handlers import (
    supporter_name,
    supporter_city,
    supporter_email,
    supporter_phone,
    supporter_feedback,
)
from bot.expert_handlers import (
    expert_name,
    expert_field,
    expert_experience,
    expert_position,
    expert_links,
    expert_why,
    build_expert_referral_link,
)
from bot.admin_handlers import expert_admin_callback
from services import sheets_service
from services.logger_service import log


# ---------- פונקציות עזר בסיסיות ----------

def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS


def parse_start_param(text: str) -> str:
    parts = text.split(" ", maxsplit=1)
    if len(parts) == 2:
        return parts[1].strip()
    return ""


def extract_joined_via_expert(start_param: str) -> str:
    if start_param.startswith("expert_"):
        return start_param.replace("expert_", "", 1)
    return ""


def build_personal_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start={user_id}"


async def send_main_menu(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id if update and update.effective_chat else None
    if chat_id is None:
        return

    user_id = update.effective_user.id if update.effective_user else 0
    text = "תפריט ראשי:\n\nבחר מה ברצונך לעשות."
    reply_markup = build_main_menu_for_user(user_id, is_admin(user_id))

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


# ---------- /start ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text.startswith("/start"):
        start_param = parse_start_param(update.message.text)
        context.user_data["start_param"] = start_param

        if start_param and not start_param.startswith("expert_"):
            context.user_data["referrer"] = start_param

        joined = extract_joined_via_expert(start_param)
        if joined:
            context.user_data["joined_via_expert_id"] = joined

    await log(context, "Start command", user=update.effective_user, extra={
        "start_param": context.user_data.get("start_param")
    })

    context.user_data["user_id"] = update.effective_user.id
    context.user_data["username"] = update.effective_user.username
    context.user_data["full_name_telegram"] = update.effective_user.full_name
    context.user_data["created_at"] = datetime.utcnow().isoformat()

    intro_text = (
        "ברוך הבא לתנועת אחדות.\n\n"
        "אני הבוט שדרכו מצטרפים, נרשמים כתומכים ומגישים מועמדות כמומחים.\n\n"
        "איך תרצה להצטרף?"
    )

    if update.message:
        await update.message.reply_text(intro_text, reply_markup=build_start_keyboard())
    else:
        await update.callback_query.message.reply_text(intro_text, reply_markup=build_start_keyboard())

    return CHOOSING_ROLE


# ---------- פקודות בסיס ----------

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log(context, "Menu command", user=update.effective_user)
    await send_main_menu(update, context)


async def all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log(context, "All commands requested", user=update.effective_user)
    text = (
        "פקודות זמינות:\n\n"
        "/start – התחלת תהליך רישום\n"
        "/menu – תפריט ראשי\n"
        "/help – עזרה\n"
        "/myid – הצגת ה-ID שלך\n"
        "/groupid – הצגת ה-ID של הקבוצה\n"
        "/positions – רשימת מקומות\n"
        "/position <מספר> – פרטי מקום\n"
        "/assign <מקום> <user_id> – שיוך מקום (אדמין)\n"
        "/reset_position <מקום> – איפוס מקום (אדמין)\n"
        "/reset_all_positions – איפוס כל המקומות (אדמין)\n"
        "/find_user <user_id> – חיפוש משתמש\n"
        "/find_expert <user_id> – חיפוש מומחה\n"
        "/find_position <id> – חיפוש מקום\n"
        "/list_approved_experts – מומחים מאושרים\n"
        "/list_rejected_experts – מומחים שנדחו\n"
        "/list_supporters – רשימת תומכים\n"
        "/support <טקסט> – שליחת פנייה לתמיכה\n"
        "/set_expert_group <user_id> <link> – שמירת קישור קבוצה למומחה\n"
        "/admin_menu – פאנל אדמין\n"
    )
    await update.message.reply_text(text)


# ---------- בחירת תפקיד ב־callback ----------

async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    role = query.data
    context.user_data["role"] = role
    context.user_data["user_id"] = query.from_user.id
    context.user_data["username"] = query.from_user.username
    context.user_data["full_name_telegram"] = query.from_user.full_name
    context.user_data["created_at"] = datetime.utcnow().isoformat()

    await log(context, "Role chosen", user=query.from_user, extra={
        "role": role,
        "created_at": context.user_data["created_at"],
    })

    if role == ROLE_SUPPORTER:
        await query.edit_message_text("מה שמך המלא?")
        return SUPPORTER_NAME

    if role == ROLE_EXPERT:
        await query.edit_message_text("מה שמך המלא?")
        return EXPERT_NAME


# ---------- callbacks של תפריטים ----------

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot import admin_handlers  # למניעת import מעגלי
    query = update.callback_query
    await query.answer()
    user = query.from_user
    bot_username = context.bot.username

    # תפריט ראשי
    if query.data == CALLBACK_MENU_MAIN:
        await log(context, "Open main menu (callback)", user=user)
        await send_main_menu(update, context)
        return

    # תפריט תומך
    if query.data == CALLBACK_MENU_SUPPORT:
        await log(context, "Open supporter menu", user=user)

        supporter = sheets_service.get_supporter_by_id(str(user.id))
        personal_link = build_personal_link(bot_username, user.id)

        if supporter:
            text = (
                "פרופיל תומך:\n\n"
                f"שם: {supporter.get('full_name_telegram', user.full_name)}\n"
                f"עיר: {supporter.get('city', 'לא צויין')}\n"
                f"אימייל: {supporter.get('email', 'לא צויין')}\n\n"
                "הקישור האישי שלך לשיתוף:\n"
                f"{personal_link}\n\n"
                "מה תרצה לעשות עכשיו?"
            )
        else:
            text = (
                "עדיין לא נרשמת כתומך.\n\n"
                "כדי להירשם כתומך:\n"
                "שלח /start ובחר 'תומך'.\n\n"
                "אחרי ההרשמה תקבל קישור אישי לשיתוף."
            )

        keyboard = build_supporter_profile_keyboard(personal_link)
        await query.edit_message_text(text, reply_markup=keyboard)
        return

    # תפריט מומחה
    if query.data == CALLBACK_MENU_EXPERT:
        await log(context, "Open expert menu", user=user)

        status = sheets_service.get_expert_status(str(user.id))
        position = sheets_service.get_expert_position(str(user.id))
        group_link = sheets_service.get_expert_group_link(str(user.id))
        referral_link = build_expert_referral_link(bot_username, user.id)

        if status is None:
            text = (
                "עדיין לא הגשת מועמדות כמומחה.\n\n"
                "כדי להגיש מועמדות:\n"
                "שלח /start ובחר 'מומחה'."
            )
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🧠 הגשת מועמדות כמומחה", callback_data=CALLBACK_APPLY_EXPERT)],
                [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
            ])
            await query.edit_message_text(text, reply_markup=keyboard)
            return

        status_text_map = {
            "pending": "ממתין לאישור",
            "approved": "מאושר",
            "rejected": "נדחה",
        }
        status_text = status_text_map.get(status, status or "לא ידוע")
        pos_text = position or "לא נבחר"

        text = (
            "פאנל מומחה:\n\n"
            f"סטטוס המועמדות שלך: {status_text}\n"
            f"מקום שבחרת: {pos_text}\n\n"
        )

        from telegram import InlineKeyboardButton

        if status == "approved":
            text += (
                "המועמדות שלך אושרה.\n\n"
                "קישור הבוט האישי שלך לשיתוף (מומחה):\n"
                f"{referral_link}\n\n"
            )
            if group_link:
                text += f"קישור לקבוצה שלך:\n{group_link}\n\n"
            else:
                text += (
                    "עדיין לא הוגדר קישור לקבוצה שלך.\n"
                    "האדמין יכול להגדיר זאת עם:\n"
                    "/set_expert_group <user_id> <link>\n\n"
                )
        elif status == "pending":
            text += "המועמדות שלך ממתינה לאישור אדמין.\n\n"
        elif status == "rejected":
            text += (
                "המועמדות שלך נדחתה.\n"
                "תוכל להגיש מועמדות מחדש בכל עת.\n\n"
            )

        text += "מה תרצה לעשות עכשיו?"

        keyboard = build_expert_panel_keyboard(status, referral_link)
        await query.edit_message_text(text, reply_markup=keyboard)
        return

    # תפריט אדמין
    if query.data == CALLBACK_MENU_ADMIN:
        if not is_admin(user.id):
            await query.edit_message_text("אין לך הרשאה לצפות בפאנל האדמין.")
            return

        await log(context, "Open admin panel", user=user)
        text = (
            "פאנל אדמין:\n\n"
            "פקודות מרכזיות:\n"
            "/positions – צפייה ברשימת כל המקומות\n"
            "/position <מספר> – פרטי מקום ספציפי\n"
            "/assign <מקום> <user_id> – שיוך מקום למשתמש\n"
            "/reset_position <מספר> – איפוס מקום יחיד\n"
            "/reset_all_positions – איפוס כל המקומות\n"
            "/set_expert_group <user_id> <link> – הגדרת קבוצה למומחה\n\n"
            "כלי חיפוש:\n"
            "/find_user <user_id>\n"
            "/find_expert <user_id>\n"
            "/find_position <id>\n"
            "/list_approved_experts\n"
            "/list_rejected_experts\n"
            "/list_supporters\n"
        )
        await query.edit_message_text(text, reply_markup=build_admin_panel_keyboard())
        return

    # מומחים ממתינים
    if query.data == CALLBACK_ADMIN_PENDING_EXPERTS:
        if not is_admin(user.id):
            await query.edit_message_text("אין לך הרשאה.")
            return

        await log(context, "Admin view pending experts", user=user)
        experts = sheets_service.get_experts_pending()

        from telegram import InlineKeyboardMarkup, InlineKeyboardButton

        if not experts:
            await query.edit_message_text(
                "אין מומחים ממתינים כרגע.",
                reply_markup=build_main_menu_for_user(user.id, is_admin(user.id))
            )
            return

        text = "מומחים ממתינים:\n\n"
        keyboard_rows = []

        for expert in experts:
            text += (
                f"{expert['expert_full_name']} – מקום {expert['expert_position']}, "
                f"תחום: {expert['expert_field']}\n"
            )
            keyboard_rows.append([
                InlineKeyboardButton(
                    f"אשר {expert['expert_full_name']}",
                    callback_data=f"expert_approve:{expert['user_id']}",
                ),
                InlineKeyboardButton(
                    "דחה",
                    callback_data=f"expert_reject:{expert['user_id']}",
                ),
            ])

        keyboard_rows.append(
            [InlineKeyboardButton("↩️ חזרה לפאנל אדמין", callback_data=CALLBACK_MENU_ADMIN)]
        )

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard_rows),
        )
        return

    # ניהול קבוצות
    if query.data == CALLBACK_ADMIN_GROUPS:
        from utils.constants import (
            ALL_MEMBERS_GROUP_ID,
            ACTIVISTS_GROUP_ID,
            EXPERTS_GROUP_ID,
            SUPPORT_GROUP_ID,
        )
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton

        if not is_admin(user.id):
            await query.edit_message_text("אין לך הרשאה.")
            return

        await log(context, "Admin view groups info", user=user)

        text = (
            "ניהול קבוצות:\n\n"
            f"ALL_MEMBERS_GROUP_ID: {ALL_MEMBERS_GROUP_ID or 'לא מוגדר'}\n"
            f"ACTIVISTS_GROUP_ID: {ACTIVISTS_GROUP_ID or 'לא מוגדר'}\n"
            f"EXPERTS_GROUP_ID: {EXPERTS_GROUP_ID or 'לא מוגדר'}\n"
            f"SUPPORT_GROUP_ID: {SUPPORT_GROUP_ID or 'לא מוגדר'}\n\n"
            "ניתן לעדכן את הערכים דרך משתני סביבה (ENV) בפריסה."
        )
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ חזרה לפאנל אדמין", callback_data=CALLBACK_MENU_ADMIN)],
                [InlineKeyboardButton("↩️ תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
            ]),
        )
        return

    # apply מחדש / התחלת תהליך מומחה מחדש
    if query.data == CALLBACK_APPLY_EXPERT:
        await log(context, "User chose apply expert from menu", user=user)
        await query.edit_message_text("כדי להגיש מועמדות כמומחה:\nשלח /start ובחר 'מומחה'.")
        return

    if query.data == CALLBACK_APPLY_SUPPORTER:
        await log(context, "User chose re-apply supporter", user=user)
        await query.edit_message_text("מתחילים מחדש את תהליך ההרשמה.\nשלח /start ובחר 'תומך'.")
        return

    # רשימת מקומות מתוך תפריט
    if query.data == CALLBACK_MENU_POSITIONS:
        positions = sheets_service.get_positions()
        await log(context, "View positions from menu", user=user, extra={
            "positions_count": len(positions)
        })
        text = "רשימת המקומות:\n\n"
        for pos in positions:
            status = "תפוס" if pos["expert_user_id"] else "פנוי"
            text += f"{pos['position_id']}. {pos['title']} - {status}\n"
        await query.edit_message_text(text, reply_markup=build_main_menu_for_user(user.id, is_admin(user.id)))
        return


# ---------- פקודות עזר ----------

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log(context, "my_id requested", user=update.effective_user)
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")


async def group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log(context, "group_id requested", user=update.effective_user, extra={
        "chat_id": update.effective_chat.id
    })
    await update.message.reply_text(f"Group ID: {update.effective_chat.id}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log(context, "Conversation cancelled", user=update.effective_user)
    await update.message.reply_text(
        "ההרשמה בוטלה.\n"
        "תוכל להתחיל מחדש בכל עת עם /start או לפתוח את התפריט עם /menu."
    )
    return ConversationHandler.END


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log(context, "Unknown command", user=update.effective_user, extra={
        "text": update.message.text
    })
    await update.message.reply_text(
        "לא זיהיתי את הפקודה הזו.\n"
        "נסה /menu כדי לראות את כל האפשרויות."
    )


# ---------- ConversationHandler ----------

def get_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            CHOOSING_ROLE: [
                CallbackQueryHandler(choose_role, pattern="^(supporter|expert)$"),
                CommandHandler("start", start),
            ],
            SUPPORTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_name),
                CommandHandler("start", start),
            ],
            SUPPORTER_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_city),
                CommandHandler("start", start),
            ],
            SUPPORTER_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_email),
                CommandHandler("start", start),
            ],
            SUPPORTER_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_phone),
                CommandHandler("start", start),
            ],
            SUPPORTER_FEEDBACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_feedback),
                CommandHandler("start", start),
            ],
            EXPERT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_name),
                CommandHandler("start", start),
            ],
            EXPERT_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_field),
                CommandHandler("start", start),
            ],
            EXPERT_EXPERIENCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_experience),
                CommandHandler("start", start),
            ],
            EXPERT_POSITION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_position),
                CommandHandler("start", start),
            ],
            EXPERT_LINKS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_links),
                CommandHandler("start", start),
            ],
            EXPERT_WHY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expert_why),
                CommandHandler("start", start),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
        per_message=False,
    )
