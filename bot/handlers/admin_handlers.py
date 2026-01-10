# ===============================
# admin_handlers – פאנל אדמין, חיפוש, רשימות, שידור
# ===============================

from datetime import datetime
from typing import Optional, Dict, List

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from services import sheets_service
from services.logger_service import log
from bot.expert_handlers import build_expert_referral_link
from bot.keyboards import build_admin_panel_keyboard, build_admin_sheets_keyboard, build_main_menu_for_user
from utils.constants import (
    ADMIN_IDS,
    SUPPORT_GROUP_ID,
    EXPERTS_GROUP_ID,
    CALLBACK_MENU_MAIN,
    CALLBACK_MENU_ADMIN,
    CALLBACK_ADMIN_SHEETS,
    CALLBACK_ADMIN_SHEETS_INFO,
    CALLBACK_ADMIN_SHEETS_FIX,
    CALLBACK_ADMIN_SHEETS_VALIDATE,
    CALLBACK_ADMIN_SHEETS_CLEAR_DUP,
    CALLBACK_ADMIN_BROADCAST,
    CALLBACK_ADMIN_EXPORT,
    CALLBACK_ADMIN_QUICK_NAV,
)


# ===============================
# עזר: בדיקת אדמין
# ===============================

def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS


# ===============================
# מקומות – פקודות אדמין
# ===============================

async def list_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    positions = sheets_service.get_positions()
    await log(context, "Admin list positions", user=user, extra={"count": len(positions)})

    if not positions:
        await update.message.reply_text("אין מקומות מוגדרים.")
        return

    text = "📊 רשימת מקומות:\n\n"
    for pos in positions:
        status = "תפוס" if pos.get("expert_user_id") else "פנוי"
        text += f"{pos.get('position_id')}. {pos.get('title')} – {status}\n"

    await update.message.reply_text(text)


async def position_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("שימוש: /position <id>")
        return

    pos_id = args[1]
    pos = sheets_service.get_position(pos_id)
    if not pos:
        await update.message.reply_text("מקום לא נמצא.")
        return

    expert_id = pos.get("expert_user_id")
    expert_name = "אין"
    if expert_id:
        expert = sheets_service.get_expert_by_id(str(expert_id))
        if expert:
            expert_name = expert.get("expert_full_name", expert_id)

    text = (
        f"🪪 מקום {pos.get('position_id')}:\n"
        f"שם: {pos.get('title')}\n"
        f"תיאור: {pos.get('description', '')}\n"
        f"מומחה: {expert_name}\n"
        f"תאריך שיוך: {pos.get('assigned_at', '—')}\n"
    )
    await update.message.reply_text(text)


async def assign_position_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    args = update.message.text.split()
    if len(args) < 3:
        await update.message.reply_text("שימוש: /assign <position_id> <user_id>")
        return

    pos_id = args[1]
    target_user_id = args[2]

    try:
        if not sheets_service.position_is_free(pos_id):
            await update.message.reply_text("המקום הזה כבר תפוס.")
            return

        now = datetime.utcnow().isoformat()
        sheets_service.assign_position(position_id=pos_id, user_id=target_user_id, timestamp=now)

        await log(context, "Admin assign position", user=user, extra={
            "position_id": pos_id,
            "expert_user_id": target_user_id,
        })
        await update.message.reply_text(f"מקום {pos_id} שויך ל־user_id {target_user_id}.")
    except Exception as e:
        await update.message.reply_text(f"שגיאה בשיוך מקום: {e}")


async def reset_position_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("שימוש: /reset_position <position_id>")
        return

    pos_id = args[1]

    try:
        sheets_service.reset_position(pos_id)
        await log(context, "Admin reset position", user=user, extra={"position_id": pos_id})
        await update.message.reply_text(f"מקום {pos_id} אופס.")
    except Exception as e:
        await update.message.reply_text(f"שגיאה באיפוס מקום: {e}")


async def reset_all_positions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    try:
        sheets_service.reset_all_positions()
        await log(context, "Admin reset all positions", user=user)
        await update.message.reply_text("כל המקומות אופסו.")
    except Exception as e:
        await update.message.reply_text(f"שגיאה באיפוס כל המקומות: {e}")


# ===============================
# שיטס – פקודות אדמין
# ===============================

async def fix_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await update.message.reply_text("🔧 מריץ תיקון כותרות בגיליונות...")
    try:
        sheets_service.auto_fix_all_sheets()
        await log(context, "Admin fix sheets", user=user)
        await update.message.reply_text("✔ תיקון כותרות בוצע בהצלחה.")
    except Exception as e:
        await update.message.reply_text(f"❌ שגיאה בתיקון הכותרות:\n{e}")


async def validate_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    await update.message.reply_text("✔ בודק מבנה גיליונות...")
    try:
        sheets_service.validate_all_sheets()
        await log(context, "Admin validate sheets", user=user)
        await update.message.reply_text("✔ כל הגיליונות תקינים.")
    except Exception as e:
        await update.message.reply_text(f"❌ בעיה במבנה הגיליונות:\n{e}")


async def sheet_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    users_sheet = sheets_service.get_users_sheet()
    experts_sheet = sheets_service.get_experts_sheet()
    positions_sheet = sheets_service.get_positions_sheet()

    users = sheets_service.get_sheet_info(users_sheet)
    experts = sheets_service.get_sheet_info(experts_sheet)
    positions = sheets_service.get_sheet_info(positions_sheet)

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

    await update.message.reply_text(text, parse_mode="Markdown")


async def clear_expert_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    deleted = sheets_service.clear_expert_duplicates()
    await log(context, "Admin clear expert duplicates", user=user, extra={"deleted": deleted})
    await update.message.reply_text(f"✔ נמחקו {deleted} כפילויות ממומחים.")


async def clear_user_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    deleted = sheets_service.clear_user_duplicates()
    await log(context, "Admin clear user duplicates", user=user, extra={"deleted": deleted})
    await update.message.reply_text(f"✔ נמחקו {deleted} כפילויות מתומכים.")


# ===============================
# חיפוש / רשימות
# ===============================

async def find_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("שימוש: /find_user <user_id>")
        return

    target_id = args[1]
    supporter = sheets_service.get_supporter_by_id(target_id)

    if not supporter:
        await update.message.reply_text("משתמש לא נמצא בגיליון Users.")
        return

    text = (
        f"🧑‍🎓 משתמש {target_id}:\n"
        f"שם: {supporter.get('full_name_telegram', '')}\n"
        f"עיר: {supporter.get('city', '')}\n"
        f"אימייל: {supporter.get('email', '')}\n"
        f"תפקיד: {supporter.get('role', '')}\n"
        f"תאריך יצירה: {supporter.get('created_at', '')}\n"
    )

    await update.message.reply_text(text)


async def find_expert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
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
    user = update.effective_user
    if not is_admin(user.id):
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

    expert_id = pos.get("expert_user_id")
    expert_name = "אין"
    if expert_id:
        expert = sheets_service.get_expert_by_id(str(expert_id))
        if expert:
            expert_name = expert.get("expert_full_name", expert_id)

    text = (
        f"🪪 מקום {pos.get('position_id')}:\n"
        f"שם: {pos.get('title')}\n"
        f"תיאור: {pos.get('description')}\n"
        f"מומחה: {expert_name}\n"
        f"תאריך שיוך: {pos.get('assigned_at', '—')}\n"
    )
    await update.message.reply_text(text)


async def list_approved_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    sheet = sheets_service.get_experts_sheet()
    rows = sheet.get_all_records()
    approved = sorted(
        [r for r in rows if r.get("status") == "approved"],
        key=lambda r: int(r.get("expert_position") or 999)
    )

    if not approved:
        await update.message.reply_text("אין מומחים מאושרים.")
        return

    text = "🧠 מומחים מאושרים:\n\n"
    for row in approved:
        full_name = row.get("expert_full_name", "")
        field = row.get("expert_field", "")
        position = row.get("expert_position", "")
        text += f"{full_name} – מקום {position}, תחום: {field}\n"

    await update.message.reply_text(text[:4000])


async def list_rejected_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    sheet = sheets_service.get_experts_sheet()
    rows = sheet.get_all_records()
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

    await update.message.reply_text(text[:4000])


async def list_supporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    sheet = sheets_service.get_users_sheet()
    rows = sheet.get_all_records()

    if not rows:
        await update.message.reply_text("אין תומכים.")
        return

    text = "🧑‍🎓 רשימת תומכים:\n\n"
    for row in rows:
        full_name = row.get("full_name_telegram", "")
        user_id = row.get("user_id", "")
        text += f"{full_name} – {user_id}\n"

    await update.message.reply_text(text[:4000])


# ===============================
# אישור/דחיית מומחים (callback)
# ===============================

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

    from utils.constants import CALLBACK_MENU_MAIN, CALLBACK_APPLY_EXPERT

    if approved:
        text = (
            "המועמדות שלך כמומחה אושרה.\n\n"
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

    try:
        await context.bot.send_message(
            chat_id=int(user_id),
            text=text,
            reply_markup=keyboard
        )
    except Exception as e:
        # המשתמש אולי חסם את הבוט, או שאין אפשרות לשלוח לו
        print(f"Failed to notify expert {user_id}: {e}")


# ===============================
# פאנל אדמין – פקודת /admin_menu
# ===============================

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
        "/list_supporters\n\n"
        "שידור:\n"
        "/broadcast_supporters <טקסט>\n"
        "/broadcast_experts <טקסט>\n"
    )

    await update.message.reply_text(text, reply_markup=build_admin_panel_keyboard())


# ===============================
# callbacks של אדמין (תתי־תפריטים)
# ===============================

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
        users_sheet = sheets_service.get_users_sheet()
        experts_sheet = sheets_service.get_experts_sheet()
        positions_sheet = sheets_service.get_positions_sheet()

        users = sheets_service.get_sheet_info(users_sheet)
        experts = sheets_service.get_sheet_info(experts_sheet)
        positions = sheets_service.get_sheet_info(positions_sheet)

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
        users_sheet = sheets_service.get_users_sheet()
        experts_sheet = sheets_service.get_experts_sheet()
        positions_sheet = sheets_service.get_positions_sheet()

        users = sheets_service.get_sheet_info(users_sheet)
        experts = sheets_service.get_sheet_info(experts_sheet)
        positions = sheets_service.get_sheet_info(positions_sheet)

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
        users_sheet = sheets_service.get_users_sheet()
        experts_sheet = sheets_service.get_experts_sheet()

        users = users_sheet.get_all_records()
        experts = experts_sheet.get_all_records()

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


# ===============================
# שידור פשוט לקבוצות (commands)
# ===============================

async def broadcast_supporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
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
    try:
        await context.bot.send_message(
            chat_id=int(SUPPORT_GROUP_ID),
            text=text,
            parse_mode="HTML",
        )
        await update.message.reply_text("✔ ההודעה נשלחה לקבוצת התומכים.")
        await log(context, "Broadcast to supporters", user=user, extra={"text": text})
    except Exception as e:
        await update.message.reply_text(f"❌ שגיאה בשליחה: {e}")


async def broadcast_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
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
    try:
        await context.bot.send_message(
            chat_id=int(EXPERTS_GROUP_ID),
            text=text,
            parse_mode="HTML",
        )
        await update.message.reply_text("✔ ההודעה נשלחה לקבוצת המומחים.")
        await log(context, "Broadcast to experts", user=user, extra={"text": text})
    except Exception as e:
        await update.message.reply_text(f"❌ שגיאה בשליחה: {e}")
