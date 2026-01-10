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
    CALLBACK_ADMIN_SHEETS,
    CALLBACK_ADMIN_SHEETS_INFO,
    CALLBACK_ADMIN_SHEETS_FIX,
    CALLBACK_ADMIN_SHEETS_VALIDATE,
    CALLBACK_ADMIN_SHEETS_CLEAR_DUP,
    CALLBACK_ADMIN_BROADCAST,
    CALLBACK_ADMIN_EXPORT,
    CALLBACK_ADMIN_QUICK_NAV,
)
from bot.keyboards import build_admin_panel_keyboard, build_admin_sheets_keyboard
from bot.expert_handlers import build_expert_referral_link


def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS


# ---------- פקודות מקומות ----------

async def list_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    positions = sheets_service.get_positions()
    await log(context, "List positions command", user=update.effective_user, extra={
        "positions_count": len(positions)
    })

    if not positions:
        await update.message.reply_text("אין מקומות מוגדרים כרגע.")
        return

    text = "📊 רשימת המקומות:\n\n"
    for pos in positions:
        status = "תפוס" if pos["expert_user_id"] else "פנוי"
        text += f"{pos['position_id']}. {pos['title']} – {status}\n"
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
        f"🪪 מקום {pos['position_id']}\n"
        f"שם: {pos['title']}\n"
        f"תיאור: {pos['description']}\n"
        f"מומחה: {pos['expert_user_id'] or 'אין'}\n"
        f"תאריך שיוך: {pos.get('assigned_at', '—')}\n"
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

    await update.message.reply_text(f"מקום {position_id} שויך ל־{target_user_id}.")


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


# ---------- שיטס: validate / fix / info / duplicates ----------

async def fix_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await update.message.reply_text("🔧 מתקן כותרות בגיליונות...")

    try:
        sheets_service.auto_fix_all_sheets()
        await update.message.reply_text("✔ כל הכותרות תוקנו בהצלחה!")
    except Exception as e:
        await update.message.reply_text(f"❌ שגיאה בתיקון הכותרות: {e}")


async def validate_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await update.message.reply_text("✔ בודק מבנה גיליונות...")

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
        "📊 מידע על הגיליונות:\n\n"
        f"*Users*\n"
        f"- כותרות: {', '.join(users['headers'])}\n"
        f"- שורות: {users['rows']}\n"
        f"- עמודות: {users['cols']}\n\n"
        f"*Experts*\n"
        f"- כותרות: {', '.join(experts['headers'])}\n"
        f"- שורות: {experts['rows']}\n"
        f"- עמודות: {experts['cols']}\n\n"
        f"*Positions*\n"
        f"- כותרות: {', '.join(positions['headers'])}\n"
        f"- שורות: {positions['rows']}\n"
        f"- עמודות: {positions['cols']}\n"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


async def clear_expert_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await update.message.reply_text("🧹 מוחק כפילויות בגיליון Experts...")

    try:
        deleted = sheets_service.clear_expert_duplicates()
        await update.message.reply_text(f"✔ נמחקו {deleted} רשומות כפולות ממומחים.")
    except Exception as e:
        await update.message.reply_text(f"❌ שגיאה במחיקת כפילויות: {e}")


async def clear_user_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await update.message.reply_text("🧹 מוחק כפילויות בגיליון Users...")

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
        f"👤 משתמש {user_id}:\n"
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
        f"🧠 מומחה {user_id}:\n"
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
        f"🪪 מקום {pos['position_id']}:\n"
        f"שם: {pos['title']}\n"
        f"תיאור: {pos['description']}\n"
        f"מומחה: {pos['expert_user_id'] or 'אין'}\n"
        f"תאריך שיוך: {pos.get('assigned_at', '—')}\n"
    )
    await update.message.reply_text(text)


async def list_approved_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    rows = sheets_service.experts_sheet.get_all_records()
    approved = [r for r in rows if r.get("status") == "approved"]

    if not approved:
        await update.message.reply_text("אין מומחים מאושרים.")
        return

    text = "🧠 מומחים מאושרים:\n\n"
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

    text = "🧠 מומחים שנדחו:\n\n"
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

    text = "🧑‍🎓 רשימת תומכים:\n\n"
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
        await query.edit_message_text("המומחה אושר.")
    else:
        sheets_service.update_expert_status(user_id, "rejected")
        await log(context, "Expert rejected", user=query.from_user, extra={
            "expert_user_id": user_id
        })
        await notify_expert(context, user_id, False)
        await query.edit_message_text("המומחה נדחה.")


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
        "🛠️ פאנל אדמין – כלים מרכזיים:\n\n"
        "מקומות:\n"
        "/positions – רשימת כל המקומות\n"
        "/position <מספר> – פרטי מקום ספציפי\n"
        "/assign <מקום> <user_id> – שיוך מקום למשתמש\n"
        "/reset_position <מספר> – איפוס מקום יחיד\n"
        "/reset_all_positions – איפוס כל המקומות\n\n"
        "שיטס:\n"
        "/sheet_info – מידע על הגיליונות\n"
        "/validate_sheets – בדיקת תקינות\n"
        "/fix_sheets – תיקון כותרות\n"
        "/clear_user_duplicates – ניקוי כפילויות מתומכים\n"
        "/clear_expert_duplicates – ניקוי כפילויות ממומחים\n\n"
        "חיפוש / רשימות:\n"
        "/find_user <user_id>\n"
        "/find_expert <user_id>\n"
        "/find_position <id>\n"
        "/list_approved_experts\n"
        "/list_rejected_experts\n"
        "/list_supporters\n"
    )

    await update.message.reply_text(text, reply_markup=build_admin_panel_keyboard())


# ---------- תתי־תפריטים של אדמין דרך callbacks ----------

async def handle_admin_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """
    נקודת ריכוז ל־callbacks של אדמין שלא קשורים למומחים ממתינים (אותם מטפלים ב־bot_handlers).
    """
    user = query.from_user

    if not is_admin(user.id):
        await query.edit_message_text("אין לך הרשאה.")
        return

    data = query.data

    # ניהול גיליונות – תפריט משנה
    if data == CALLBACK_ADMIN_SHEETS:
        users = sheets_service.get_sheet_info(sheets_service.users_sheet)
        experts = sheets_service.get_sheet_info(sheets_service.experts_sheet)
        positions = sheets_service.get_sheet_info(sheets_service.positions_sheet)

        text = (
            "📊 ניהול גיליונות:\n\n"
            f"Users – {users['rows']} שורות, {users['cols']} עמודות\n"
            f"Experts – {experts['rows']} שורות, {experts['cols']} עמודות\n"
            f"Positions – {positions['rows']} שורות, {positions['cols']} עמודות\n\n"
            "בחר פעולה:"
        )
        await query.edit_message_text(text, reply_markup=build_admin_sheets_keyboard())
        return

    # מידע על הגיליונות
    if data == CALLBACK_ADMIN_SHEETS_INFO:
        users = sheets_service.get_sheet_info(sheets_service.users_sheet)
        experts = sheets_service.get_sheet_info(sheets_service.experts_sheet)
        positions = sheets_service.get_sheet_info(sheets_service.positions_sheet)

        text = (
            "📊 מידע מפורט על הגיליונות:\n\n"
            f"*Users*\n"
            f"- כותרות: {', '.join(users['headers'])}\n"
            f"- שורות: {users['rows']}\n"
            f"- עמודות: {users['cols']}\n\n"
            f"*Experts*\n"
            f"- כותרות: {', '.join(experts['headers'])}\n"
            f"- שורות: {experts['rows']}\n"
            f"- עמודות: {experts['cols']}\n\n"
            f"*Positions*\n"
            f"- כותרות: {', '.join(positions['headers'])}\n"
            f"- שורות: {positions['rows']}\n"
            f"- עמודות: {positions['cols']}\n"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=build_admin_sheets_keyboard())
        return

    # תיקון גיליונות
    if data == CALLBACK_ADMIN_SHEETS_FIX:
        await query.edit_message_text("🔧 מריץ תיקון כותרות בגיליונות...")
        try:
            sheets_service.auto_fix_all_sheets()
            await query.edit_message_text("✔ תיקון כותרות בוצע בהצלחה.", reply_markup=build_admin_sheets_keyboard())
        except Exception as e:
            await query.edit_message_text(f"❌ שגיאה בתיקון הכותרות:\n{e}", reply_markup=build_admin_sheets_keyboard())
        return

    # בדיקת תקינות
    if data == CALLBACK_ADMIN_SHEETS_VALIDATE:
        await query.edit_message_text("✔ בודק מבנה גיליונות...")
        try:
            sheets_service.validate_all_sheets()
            await query.edit_message_text("✔ כל הגיליונות תקינים.", reply_markup=build_admin_sheets_keyboard())
        except Exception as e:
            await query.edit_message_text(f"❌ בעיה במבנה הגיליונות:\n{e}", reply_markup=build_admin_sheets_keyboard())
        return

    # ניקוי כפילויות
    if data == CALLBACK_ADMIN_SHEETS_CLEAR_DUP:
        await query.edit_message_text("🧹 מנקה כפילויות ב־Users ו־Experts...")
        try:
            u_deleted = sheets_service.clear_user_duplicates()
            e_deleted = sheets_service.clear_expert_duplicates()
            await query.edit_message_text(
                f"✔ נמחקו {u_deleted} כפילויות מתומכים ו־{e_deleted} כפילויות ממומחים.",
                reply_markup=build_admin_sheets_keyboard(),
            )
        except Exception as e:
            await query.edit_message_text(f"❌ שגיאה בניקוי כפילויות:\n{e}", reply_markup=build_admin_sheets_keyboard())
        return

    # שידור – הדרכה
    if data == CALLBACK_ADMIN_BROADCAST:
        text = (
            "📨 שליחת הודעה לתומכים / מומחים:\n\n"
            "כרגע מוגדר שידור דרך פקודות:\n"
            "- /broadcast_supporters <טקסט>\n"
            "- /broadcast_experts <טקסט>\n\n"
            "ההודעות נשלחות לקבוצות שהוגדרו ב־ENV:\n"
            f"SUPPORT_GROUP_ID: {SUPPORT_GROUP_ID or 'לא מוגדר'}\n"
            f"EXPERTS_GROUP_ID: {EXPERTS_GROUP_ID or 'לא מוגדר'}\n\n"
            "לשינוי – עדכן את משתני הסביבה."
        )
        await query.edit_message_text(text, reply_markup=build_admin_panel_keyboard())
        return

    # יצוא נתונים – טקסט
    if data == CALLBACK_ADMIN_EXPORT:
        users = sheets_service.users_sheet.get_all_records()
        experts = sheets_service.experts_sheet.get_all_records()

        text = (
            "📁 יצוא נתונים (תמציתי):\n\n"
            f"Users: {len(users)} רשומות\n"
            f"Experts: {len(experts)} רשומות\n\n"
            "להורדה מפורטת – השתמש ישירות בגוגל שיטס.\n"
        )
        await query.edit_message_text(text, reply_markup=build_admin_panel_keyboard())
        return

    # ניווט מהיר
    if data == CALLBACK_ADMIN_QUICK_NAV:
        text = (
            "🧭 ניווט מהיר לאדמין:\n\n"
            "מקומות:\n"
            "/positions\n"
            "/position <id>\n\n"
            "שיטס:\n"
            "/sheet_info\n"
            "/validate_sheets\n"
            "/fix_sheets\n\n"
            "חיפוש ורשימות:\n"
            "/find_user <user_id>\n"
            "/find_expert <user_id>\n"
            "/find_position <id>\n"
            "/list_approved_experts\n"
            "/list_rejected_experts\n"
            "/list_supporters\n\n"
            "שידור:\n"
            "/broadcast_supporters <טקסט>\n"
            "/broadcast_experts <טקסט>\n"
        )
        await query.edit_message_text(text, reply_markup=build_admin_panel_keyboard())
        return


# ---------- שידור פשוט לקבוצות (commands) ----------

async def broadcast_supporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    if not SUPPORT_GROUP_ID:
        await update.message.reply_text("SUPPORT_GROUP_ID לא מוגדר ב־ENV.")
        return

    args = update.message.text.split(" ", maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("שימוש: /broadcast_supporters <טקסט ההודעה>")
        return

    text = args[1]
    await context.bot.send_message(chat_id=int(SUPPORT_GROUP_ID), text=text)
    await update.message.reply_text("הודעה נשלחה לקבוצת התומכים.")


async def broadcast_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    if not EXPERTS_GROUP_ID:
        await update.message.reply_text("EXPERTS_GROUP_ID לא מוגדר ב־ENV.")
        return

    args = update.message.text.split(" ", maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("שימוש: /broadcast_experts <טקסט ההודעה>")
        return

    text = args[1]
    await context.bot.send_message(chat_id=int(EXPERTS_GROUP_ID), text=text)
    await update.message.reply_text("הודעה נשלחה לקבוצת המומחים.")
