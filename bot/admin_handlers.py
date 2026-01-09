# ===============================
# Handlers של אדמין (פקודות + callbacks)
# ===============================

from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from services import sheets_service
from services.logger_service import log
from utils.constants import (
    ADMIN_IDS,
    ALL_MEMBERS_GROUP_ID,
    ACTIVISTS_GROUP_ID,
    EXPERTS_GROUP_ID,
    SUPPORT_GROUP_ID,
    CALLBACK_MENU_MAIN,
    CALLBACK_MENU_POSITIONS,
    CALLBACK_ADMIN_PENDING_EXPERTS,
    CALLBACK_ADMIN_GROUPS,
)
from bot.keyboards import build_admin_panel_keyboard
from bot.expert_handlers import build_expert_referral_link


def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS


# ---------- פקודות שקשורות למקומות ----------

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


async def assign_position_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
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
    if not is_admin(update.effective_user.id):
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
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    try:
        sheets_service.reset_all_positions()
        await log(context, "All positions reset by admin", user=update.effective_user)
        await update.message.reply_text("כל המקומות אופסו.")
    except Exception as e:
        await update.message.reply_text("אירעה שגיאה בעת איפוס כל המקומות.")
        print("Error in reset_all_positions_cmd:", e)


# ---------- פקודות שקשורות לשיטס (validate/fix/info/duplicates) ----------

async def fix_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await update.message.reply_text("מתקן כותרות בגיליונות...")

    try:
        sheets_service.auto_fix_all_sheets()
        await update.message.reply_text("✔ כל הכותרות תוקנו בהצלחה!")
    except Exception as e:
        await update.message.reply_text(f"❌ שגיאה בתיקון הכותרות: {e}")


async def validate_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await update.message.reply_text("בודק מבנה גיליונות...")

    try:
        sheets_service.validate_all_sheets()
        await update.message.reply_text("✔ כל הגיליונות תקינים.")
    except Exception as e:
        await update.message.reply_text(f"❌ בעיה במבנה הגיליונות: {e}")


async def sheet_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    users = sheets_service.get_sheet_info(sheets_service.users_sheet)
    experts = sheets_service.get_sheet_info(sheets_service.experts_sheet)
    positions = sheets_service.get_sheet_info(sheets_service.positions_sheet)

    text = (
        "מידע על הגיליונות:\n\n"
        f"Users:\n"
        f"- כותרות: {', '.join(users['headers'])}\n"
        f"- שורות: {users['rows']}\n"
        f"- עמודות: {users['cols']}\n\n"
        f"Experts:\n"
        f"- כותרות: {', '.join(experts['headers'])}\n"
        f"- שורות: {experts['rows']}\n"
        f"- עמודות: {experts['cols']}\n\n"
        f"Positions:\n"
        f"- כותרות: {', '.join(positions['headers'])}\n"
        f"- שורות: {positions['rows']}\n"
        f"- עמודות: {positions['cols']}\n"
    )

    await update.message.reply_text(text)


async def clear_expert_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await update.message.reply_text("מוחק כפילויות בגיליון Experts...")

    try:
        deleted = sheets_service.clear_expert_duplicates()
        await update.message.reply_text(f"✔ נמחקו {deleted} רשומות כפולות ממומחים.")
    except Exception as e:
        await update.message.reply_text(f"❌ שגיאה במחיקת כפילויות: {e}")


async def clear_user_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await update.message.reply_text("מוחק כפילויות בגיליון Users...")

    try:
        deleted = sheets_service.clear_user_duplicates()
        await update.message.reply_text(f"✔ נמחקו {deleted} רשומות כפולות מתומכים.")
    except Exception as e:
        await update.message.reply_text(f"❌ שגיאה במחיקת כפילויות: {e}")


# ---------- חיפוש / רשימות ----------

async def find_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
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
    if not is_admin(update.effective_user.id):
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
    if not is_admin(update.effective_user.id):
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


# ---------- רשימות מומחים / תומכים (מבוסס על get_all_records במקום _load_*) ----------

async def list_approved_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    rows = sheets_service.experts_sheet.get_all_records()
    approved = [r for r in rows if r.get("status") == "approved"]

    if not approved:
        await update.message.reply_text("אין מומחים מאושרים.")
        return

    text = "מומחים מאושרים:\n\n"
    for row in approved:
        full_name = row.get("expert_full_name", "")
        field = row.get("expert_field", "")
        position = row.get("expert_position", "")
        text += f"{full_name} – מקום {position}, תחום: {field}\n"

    await update.message.reply_text(text)


async def list_rejected_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    rows = sheets_service.experts_sheet.get_all_records()
    rejected = [r for r in rows if r.get("status") == "rejected"]

    if not rejected:
        await update.message.reply_text("אין מומחים שנדחו.")
        return

    text = "מומחים שנדחו:\n\n"
    for row in rejected:
        full_name = row.get("expert_full_name", "")
        field = row.get("expert_field", "")
        position = row.get("expert_position", "")
        text += f"{full_name} – מקום {position}, תחום: {field}\n"

    await update.message.reply_text(text)


async def list_supporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    rows = sheets_service.users_sheet.get_all_records()

    if not rows:
        await update.message.reply_text("אין תומכים.")
        return

    text = "רשימת תומכים:\n\n"
    for row in rows:
        full_name = row.get("full_name_telegram", "")
        user_id = row.get("user_id", "")
        text += f"{full_name} – {user_id}\n"

    await update.message.reply_text(text)


# ---------- callbacks של אישור/דחיית מומחים + admin menu ----------

async def expert_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
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
            [InlineKeyboardButton("📋 פתיחת תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
        ])

    await context.bot.send_message(
        chat_id=int(user_id),
        text=text,
        reply_markup=keyboard
    )


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await log(context, "Admin menu command", user=user)

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

    await update.message.reply_text(text, reply_markup=build_admin_panel_keyboard())
