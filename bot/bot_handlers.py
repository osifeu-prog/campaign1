import os
from datetime import datetime
from typing import Optional

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
from bot.logger_service import log  # שכבת לוגים חכמה

# ============================================
# ============ ENV & CONSTANTS ===============
# ============================================

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
    SUPPORTER_PHONE,
    SUPPORTER_FEEDBACK,
    EXPERT_NAME,
    EXPERT_FIELD,
    EXPERT_EXPERIENCE,
    EXPERT_POSITION,
    EXPERT_LINKS,
    EXPERT_WHY,
) = range(12)

ROLE_SUPPORTER = "supporter"
ROLE_EXPERT = "expert"

CALLBACK_MENU_MAIN = "menu_main"
CALLBACK_MENU_SUPPORT = "menu_support"
CALLBACK_MENU_EXPERT = "menu_expert"
CALLBACK_MENU_ADMIN = "menu_admin"
CALLBACK_APPLY_EXPERT = "apply_expert_again"
CALLBACK_APPLY_SUPPORTER = "apply_supporter"
CALLBACK_ADMIN_PENDING_EXPERTS = "admin_pending_experts"
CALLBACK_ADMIN_GROUPS = "admin_groups"

# ============================================
# =============== HELPERS ====================
# ============================================

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


def build_expert_referral_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start=expert_{user_id}"


def build_main_menu_for_user(user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🧑‍🎓 הרשמה / פרופיל תומך", callback_data=CALLBACK_MENU_SUPPORT)],
        [InlineKeyboardButton("🧠 פאנל מומחה", callback_data=CALLBACK_MENU_EXPERT)],
        [InlineKeyboardButton("📊 רשימת מקומות", callback_data="menu_positions")],
        [InlineKeyboardButton("🆘 תמיכה", callback_data=CALLBACK_MENU_SUPPORT)],
    ]

    if is_admin(user_id):
        buttons.append([InlineKeyboardButton("🛠️ פאנל אדמין", callback_data=CALLBACK_MENU_ADMIN)])

    return InlineKeyboardMarkup(buttons)


async def send_main_menu(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id if update and update.effective_chat else None
    if chat_id is None:
        return

    user_id = update.effective_user.id if update.effective_user else 0
    text = "תפריט ראשי:\n\nבחר מה ברצונך לעשות."
    reply_markup = build_main_menu_for_user(user_id)

    if update.callback_query:
        await update.callback_query.edit_text(text, reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


# ============================================
# ================= MENU =====================
# ============================================

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

    intro_text = (
        "ברוך הבא לתנועת אחדות.\n\n"
        "אני הבוט שדרכו מצטרפים, נרשמים כתומכים ומגישים מועמדות כמומחים.\n\n"
        "איך תרצה להצטרף?"
    )

    keyboard = [
        [
            InlineKeyboardButton("🧠 אני מומחה", callback_data=ROLE_EXPERT),
            InlineKeyboardButton("🧑‍🎓 אני תומך", callback_data=ROLE_SUPPORTER),
        ],
        [InlineKeyboardButton("📋 פתח תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ]

    if update.message:
        await update.message.reply_text(intro_text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(intro_text, reply_markup=InlineKeyboardMarkup(keyboard))

    return CHOOSING_ROLE


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


# ============================================
# =========== SUPPORTER FLOW =================
# ============================================

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


async def supporter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_full_name"] = update.message.text.strip()
    await log(context, "Supporter name entered", user=update.effective_user)
    await update.message.reply_text("באיזו עיר אתה גר?")
    return SUPPORTER_CITY


async def supporter_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_city"] = update.message.text.strip()
    await log(context, "Supporter city entered", user=update.effective_user)
    await update.message.reply_text("כתובת אימייל (אפשר 'דלג'):")
    return SUPPORTER_EMAIL


async def supporter_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["supporter_email"] = "" if text.lower() in ["דלג", "skip"] else text

    await log(context, "Supporter email entered", user=update.effective_user)
    await update.message.reply_text("מה מספר הטלפון שלך?")
    return SUPPORTER_PHONE


async def supporter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_phone"] = update.message.text.strip()
    await log(context, "Supporter phone entered", user=update.effective_user)
    await update.message.reply_text("מה גרם לך להצטרף לתנועה?")
    return SUPPORTER_FEEDBACK


async def supporter_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["supporter_feedback"] = update.message.text.strip()

    user_row = {
        "user_id": context.user_data.get("user_id"),
        "username": context.user_data.get("username"),
        "full_name_telegram": context.user_data.get("full_name_telegram"),
        "role": ROLE_SUPPORTER,
        "city": context.user_data.get("supporter_city"),
        "email": context.user_data.get("supporter_email"),
        "referrer": context.user_data.get("referrer", ""),
        "joined_via_expert_id": context.user_data.get("joined_via_expert_id", ""),
        "created_at": context.user_data.get("created_at"),
    }

    sheets_service.append_user_row(user_row)
    await log(context, "Supporter registered", user=update.effective_user)

    personal_link = build_personal_link(context.bot.username, context.user_data["user_id"])

    text = (
        "תודה שנרשמת כתומך! 🙌\n\n"
        "זהו קישור אישי שתוכל לשתף עם חברים ומשפחה:\n"
        f"{personal_link}\n\n"
        "מה תרצה לעשות עכשיו?"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 לשתף את הקישור שלי", url=personal_link)],
        [InlineKeyboardButton("🧠 להגיש מועמדות כמומחה", callback_data=CALLBACK_APPLY_EXPERT)],
        [InlineKeyboardButton("📋 פתיחת תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ])

    await update.message.reply_text(text, reply_markup=keyboard)
    return ConversationHandler.END


# ============================================
# ================== MENU CALLBACKS ==========
# ============================================

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📣 לשתף את הקישור שלי", url=personal_link)],
            [InlineKeyboardButton("🧠 להגיש מועמדות כמומחה", callback_data=CALLBACK_MENU_EXPERT)],
            [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
        ])

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

        buttons = []
        if status == "approved":
            buttons.append([InlineKeyboardButton("📣 לשתף את הקישור שלי", url=referral_link)])
        if status in ("rejected", "approved"):
            buttons.append([InlineKeyboardButton("🧠 הגשת מועמדות מחדש", callback_data=CALLBACK_APPLY_EXPERT)])
        buttons.append([InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)])

        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(text, reply_markup=keyboard)
        return

    # תפריט אדמין
    if query.data == CALLBACK_MENU_ADMIN:
        if not is_admin(user.id):
            await query.edit_message_text("אין לך הרשאה לצפות בפאנל האדמין.")
            return

        await log(context, "Open admin panel", user=user)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 מומחים ממתינים", callback_data=CALLBACK_ADMIN_PENDING_EXPERTS)],
            [InlineKeyboardButton("📊 רשימת מקומות", callback_data="menu_positions")],
            [InlineKeyboardButton("🧩 ניהול קבוצות", callback_data=CALLBACK_ADMIN_GROUPS)],
            [InlineKeyboardButton("↩️ תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
        ])

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
        await query.edit_message_text(text, reply_markup=keyboard)
        return

    # מומחים ממתינים
    if query.data == CALLBACK_ADMIN_PENDING_EXPERTS:
        if not is_admin(user.id):
            await query.edit_message_text("אין לך הרשאה.")
            return

        await log(context, "Admin view pending experts", user=user)
        experts = sheets_service.get_experts_pending()

        if not experts:
            await query.edit_message_text(
                "אין מומחים ממתינים כרגע.",
                reply_markup=build_main_menu_for_user(user.id)
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

    # מידע על קבוצות
    if query.data == CALLBACK_ADMIN_GROUPS:
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
    if query.data == "menu_positions":
        positions = sheets_service.get_positions()
        await log(context, "View positions from menu", user=user, extra={
            "positions_count": len(positions)
        })
        text = "רשימת המקומות:\n\n"
        for pos in positions:
            status = "תפוס" if pos["expert_user_id"] else "פנוי"
            text += f"{pos['position_id']}. {pos['title']} - {status}\n"
        await query.edit_message_text(text, reply_markup=build_main_menu_for_user(user.id))
        return


# ============================================
# ============ EXPERT FLOW ===================
# ============================================

async def expert_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_full_name"] = update.message.text.strip()
    await log(context, "Expert full name entered", user=update.effective_user, extra={
        "expert_full_name": context.user_data["expert_full_name"]
    })
    await update.message.reply_text("מה תחום המומחיות שלך?")
    return EXPERT_FIELD


async def expert_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_field"] = update.message.text.strip()
    await log(context, "Expert field entered", user=update.effective_user, extra={
        "expert_field": context.user_data["expert_field"]
    })
    await update.message.reply_text("ספר בקצרה על הניסיון שלך:")
    return EXPERT_EXPERIENCE


async def expert_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_experience"] = update.message.text.strip()
    await log(context, "Expert experience entered", user=update.effective_user)
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
        await update.message.reply_text("המקום שבחרת תפוס. בחר מספר אחר.")
        return EXPERT_POSITION

    context.user_data["expert_position"] = str(pos_num)

    sheets_service.assign_position(
        position_id=str(pos_num),
        user_id=str(context.user_data.get("user_id")),
        timestamp=context.user_data.get("created_at"),
    )

    await log(context, "Expert position chosen and assigned", user=update.effective_user, extra={
        "position_id": pos_num
    })

    await update.message.reply_text(
        "המקום נרשם עבורך.\n"
        "הוסף קישורים (לינקדאין, אתר, מאמרים):"
    )
    return EXPERT_LINKS


async def expert_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expert_links"] = update.message.text.strip()
    await log(context, "Expert links entered", user=update.effective_user)
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
        "joined_via_expert_id": context.user_data.get("joined_via_expert_id", ""),
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
        "group_link": "",
    }

    sheets_service.append_user_row(user_row)
    sheets_service.append_expert_row(expert_row)

    await log(context, "Expert application submitted", user=update.effective_user, extra={
        "expert_full_name": expert_row["expert_full_name"],
        "expert_field": expert_row["expert_field"],
        "expert_position": expert_row["expert_position"],
    })

    if LOG_GROUP_ID:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("אישור", callback_data=f"expert_approve:{expert_row['user_id']}"),
                InlineKeyboardButton("דחייה", callback_data=f"expert_reject:{expert_row['user_id']}"),
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

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 פתיחת תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
        [InlineKeyboardButton("ℹ️ לראות את פאנל המומחה שלי", callback_data=CALLBACK_MENU_EXPERT)],
    ])

    await update.message.reply_text(
        "תודה! בקשה לאישור נשלחה.\n"
        "נעדכן אותך כאן ברגע שהבקשה תאושר או תידחה.\n\n"
        "בינתיים, מה תרצה לעשות?",
        reply_markup=keyboard,
    )
    return ConversationHandler.END


# ============================================
# ============== ADMIN CALLBACKS =============
# ============================================

async def expert_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if str(query.from_user.id) not in ADMIN_IDS:
        await query.edit_message_text("אין לך הרשאה.")
        return

    action, user_id = query.data.split(":")

    if action == "expert_approve":
        sheets_service.update_expert_status(user_id, "approved")
        await log(context, "Expert approved", user=query.from_user, extra={
            "expert_user_id": user_id
        })
        await notify_expert(context, user_id, True)
        await query.edit_message_text("אושר.")
    else:
        sheets_service.update_expert_status(user_id, "rejected")
        await log(context, "Expert rejected", user=query.from_user, extra={
            "expert_user_id": user_id
        })
        await notify_expert(context, user_id, False)
        await query.edit_message_text("נדחה.")


async def notify_expert(context: ContextTypes.DEFAULT_TYPE, user_id: str, approved: bool):
    bot_username = context.bot.username
    referral_link = build_expert_referral_link(bot_username, int(user_id))
    group_link = sheets_service.get_expert_group_link(user_id)

    if approved:
        text = (
            "המועמדות שלך כמומחה אושרה. 🎉\n\n"
            "זהו קישור הבוט האישי שלך לשיתוף:\n"
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

        text += "מה תרצה לעשות עכשיו?"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📣 לשתף את הקישור שלי", url=referral_link)],
            [InlineKeyboardButton("📋 פתיחת תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
        ])
    else:
        text = (
            "המועמדות שלך כמומחה לא אושרה.\n\n"
            "תוכל להגיש מועמדות מחדש בכל עת.\n"
            "כדי להתחיל מחדש, שלח /start ובחר 'מומחה'."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🧠 הגשת מועמדות מחדש", callback_data=CALLBACK_APPLY_EXPERT)],
            [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
        ])

    await context.bot.send_message(
        chat_id=int(user_id),
        text=text,
        reply_markup=keyboard
    )


# ============================================
# =========== ADMIN COMMANDS =================
# ============================================

async def list_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    positions = sheets_service.get_positions()
    await log(context, "List positions command", user=update.effective_user, extra={
        "positions_count": len(positions)
    })
    text = "רשימת המקומות:\n\n"
    for pos in positions:
        status = "תפוס" if pos["expert_user_id"] else "פנוי"
        text += f"{pos['position_id']}. {pos['title']} - {status}\n"
    await update.message.reply_text(text)


async def position_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("שימוש: /position <מספר>")
        return

    pos_id = args[1]
    pos = sheets_service.get_position(pos_id)

    await log(context, "Position details requested", user=update.effective_user, extra={
        "position_id": pos_id,
        "found": bool(pos)
    })

    if not pos:
        await update.message.reply_text("מקום לא נמצא.")
        return

    text = (
        f"מקום {pos['position_id']}\n"
        f"שם: {pos['title']}\n"
        f"תיאור: {pos['description']}\n"
        f"מומחה: {pos['expert_user_id'] or 'אין'}"
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

    position_id = args[1]
    target_user_id = args[2]

    sheets_service.assign_position(position_id, target_user_id, datetime.utcnow().isoformat())

    await log(context, "Position assigned via admin", user=update.effective_user, extra={
        "position_id": position_id,
        "assigned_to": target_user_id
    })

    await update.message.reply_text("בוצע.")


async def reset_position_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("אין לך הרשאה.")
        return

    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("שימוש: /reset_position <position_id>")
        return

    position_id = args[1].strip()

    try:
        sheets_service.reset_position(position_id)
        await log(context, "Position reset by admin", user=update.effective_user, extra={
            "position_id": position_id
        })
        await update.message.reply_text(f"מקום {position_id} אופס.")
    except ValueError:
        await update.message.reply_text("המקום לא נמצא.")
    except Exception as e:
        await update.message.reply_text("אירעה שגיאה בעת איפוס המקום.")
        print("Error in reset_position_cmd:", e)


async def reset_all_positions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("אין לך הרשאה.")
        return

    try:
        sheets_service.reset_all_positions()
        await log(context, "All positions reset by admin", user=update.effective_user)
        await update.message.reply_text("כל המקומות אופסו.")
    except Exception as e:
        await update.message.reply_text("אירעה שגיאה בעת איפוס כל המקומות.")
        print("Error in reset_all_positions_cmd:", e)


# ============================================
# =========== SEARCH COMMANDS ================
# ============================================

async def find_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("אין לך הרשאה.")
        return

    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("שימוש: /find_user <user_id>")
        return

    user_id = args[1]
    user = sheets_service.get_supporter_by_id(user_id)

    if not user:
        await update.message.reply_text("משתמש לא נמצא.")
        return

    text = (
        f"משתמש {user_id}:\n"
        f"שם: {user.get('full_name_telegram', '')}\n"
        f"עיר: {user.get('city', '')}\n"
        f"אימייל: {user.get('email', '')}\n"
        f"מצטרף דרך מומחה: {user.get('joined_via_expert_id', '')}\n"
    )
    await update.message.reply_text(text)


async def find_expert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("אין לך הרשאה.")
        return

    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("שימוש: /find_expert <user_id>")
        return

    user_id = args[1]
    expert = sheets_service.get_expert_by_id(user_id)

    if not expert:
        await update.message.reply_text("מומחה לא נמצא.")
        return

    text = (
        f"מומחה {user_id}:\n"
        f"שם: {expert.get('expert_full_name', '')}\n"
        f"תחום: {expert.get('expert_field', '')}\n"
        f"ניסיון: {expert.get('expert_experience', '')}\n"
        f"מקום: {expert.get('expert_position', '')}\n"
        f"סטטוס: {expert.get('status', '')}\n"
        f"קבוצה: {expert.get('group_link', '')}\n"
    )
    await update.message.reply_text(text)


async def find_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("אין לך הרשאה.")
        return

    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("שימוש: /find_position <id>")
        return

    pos_id = args[1]
    pos = sheets_service.get_position(pos_id)

    if not pos:
        await update.message.reply_text("מקום לא נמצא.")
        return

    text = (
        f"מקום {pos['position_id']}:\n"
        f"שם: {pos['title']}\n"
        f"תיאור: {pos['description']}\n"
        f"מומחה: {pos['expert_user_id'] or 'אין'}\n"
        f"תאריך שיוך: {pos.get('assigned_at', '—')}\n"
    )
    await update.message.reply_text(text)


async def list_approved_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("אין לך הרשאה.")
        return

    all_rows = sheets_service._load_experts_rows()
    approved = [row for row in all_rows[1:] if len(row) > 8 and row[8] == "approved"]

    if not approved:
        await update.message.reply_text("אין מומחים מאושרים.")
        return

    text = "מומחים מאושרים:\n\n"
    for row in approved:
        full_name = row[1] if len(row) > 1 else ""
        field = row[2] if len(row) > 2 else ""
        position = row[4] if len(row) > 4 else ""
        text += f"{full_name} – מקום {position}, תחום: {field}\n"

    await update.message.reply_text(text)


async def list_rejected_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("אין לך הרשאה.")
        return

    all_rows = sheets_service._load_experts_rows()
    rejected = [row for row in all_rows[1:] if len(row) > 8 and row[8] == "rejected"]

    if not rejected:
        await update.message.reply_text("אין מומחים שנדחו.")
        return

    text = "מומחים שנדחו:\n\n"
    for row in rejected:
        full_name = row[1] if len(row) > 1 else ""
        field = row[2] if len(row) > 2 else ""
        position = row[4] if len(row) > 4 else ""
        text += f"{full_name} – מקום {position}, תחום: {field}\n"

    await update.message.reply_text(text)


async def list_supporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("אין לך הרשאה.")
        return

    rows = sheets_service._load_users_rows()

    if len(rows) < 2:
        await update.message.reply_text("אין תומכים.")
        return

    text = "רשימת תומכים:\n\n"
    for row in rows[1:]:
        full_name = row[2] if len(row) > 2 else ""
        user_id = row[0] if len(row) > 0 else ""
        text += f"{full_name} – {user_id}\n"

    await update.message.reply_text(text)


# ============================================
# =========== SUPPORT / GROUP SETTING ========
# ============================================

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not SUPPORT_GROUP_ID:
        await update.message.reply_text("קבוצת התמיכה לא מוגדרת.")
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

    await log(context, "Support request sent", user=user)
    await update.message.reply_text("הפנייה נשלחה לצוות התמיכה. נחזור אליך בהקדם.")


async def set_expert_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) not in ADMIN_IDS:
        await update.message.reply_text("אין לך הרשאה.")
        return

    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("שימוש: /set_expert_group <expert_user_id> <group_link>")
        return

    expert_user_id = parts[1].strip()
    group_link = parts[2].strip()

    sheets_service.update_expert_group_link(expert_user_id, group_link)

    await log(context, "Expert group link set", user=update.effective_user, extra={
        "expert_user_id": expert_user_id,
        "group_link": group_link
    })

    await update.message.reply_text("קישור נשמר.\nהמומחה יקבל את הקישור בהודעה אישית.")


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await log(context, "Admin menu command", user=user)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 מומחים ממתינים", callback_data=CALLBACK_ADMIN_PENDING_EXPERTS)],
        [InlineKeyboardButton("📊 רשימת מקומות", callback_data="menu_positions")],
        [InlineKeyboardButton("🧩 ניהול קבוצות", callback_data=CALLBACK_ADMIN_GROUPS)],
        [InlineKeyboardButton("↩️ תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ])

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

    await update.message.reply_text(text, reply_markup=keyboard)


# ============================================
# =========== BASIC UTIL COMMANDS ============
# ============================================

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log(context, "my_id requested", user=update.effective_user)
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")


async def group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log(context, "group_id requested", user=update.effective_user, extra={
        "chat_id": update.effective_chat.id
    })
    await update.message.reply_text(f"Group ID: {update.effective_chat.id}")


# ============================================
# =========== UNKNOWN & CANCEL ===============
# ============================================

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


# ============================================
# ===== CONVERSATION HANDLER FACTORY =========
# ============================================

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
