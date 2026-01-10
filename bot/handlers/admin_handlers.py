# bot/handlers/admin_handlers.py
# ==========================================
# פקודות אדמין: מקומות, שיטס, חיפוש, שידור, ניטור
# ==========================================

from telegram import Update
from telegram.ext import ContextTypes

from utils.constants import ADMIN_IDS, DEFAULT_PAGE_SIZE
from services import sheets_service
from services.logger_service import log


def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS


# ===============================
# Positions
# ===============================

async def list_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    positions = sheets_service.get_positions()
    text = "רשימת מקומות:\n"
    for pos in positions:
        assigned = pos.get("expert_user_id") or "free"
        text += f"- {pos.get('position_id')} : assigned_to={assigned}\n"

    await update.message.reply_text(text)


async def position_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    args = context.args
    if not args:
        return await update.message.reply_text("שימוש: /position <id>")

    pos = sheets_service.get_position(args[0])
    if not pos:
        return await update.message.reply_text("מקום לא נמצא.")

    await update.message.reply_text(str(pos))


async def assign_position_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    if len(context.args) < 2:
        return await update.message.reply_text("שימוש: /assign <position_id> <user_id>")

    pos_id, user_id = context.args[0], context.args[1]
    sheets_service.assign_position(pos_id, user_id)
    await update.message.reply_text("המקום הוקצה.")


async def reset_position_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    if not context.args:
        return await update.message.reply_text("שימוש: /reset_position <id>")

    sheets_service.reset_position(context.args[0])
    await update.message.reply_text("המקום אופס.")


async def reset_all_positions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    sheets_service.reset_all_positions()
    await update.message.reply_text("כל המקומות אופסו.")


# ===============================
# Sheets
# ===============================

async def fix_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    sheets_service.auto_fix_all_sheets()
    await update.message.reply_text("תיקון גיליונות הושלם.")


async def validate_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    sheets_service.validate_all_sheets()
    await update.message.reply_text("ולידציה הושלמה.")


async def sheet_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    users = sheets_service.get_users_sheet()
    experts = sheets_service.get_experts_sheet()
    positions = sheets_service.get_positions_sheet()

    text = (
        "מידע על הגיליונות:\n\n"
        f"Users: {sheets_service.get_sheet_info(users)}\n"
        f"Experts: {sheets_service.get_sheet_info(experts)}\n"
        f"Positions: {sheets_service.get_sheet_info(positions)}\n"
    )
    await update.message.reply_text(text)


async def clear_user_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    count = sheets_service.clear_user_duplicates()
    await update.message.reply_text(f"הוסרו {count} כפילויות משתמשים.")


async def clear_expert_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    count = sheets_service.clear_expert_duplicates()
    await update.message.reply_text(f"הוסרו {count} כפילויות מומחים.")


async def backup_sheets_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("גיבוי לא נתמך בגרסה זו (דורש googleapiclient).")


# ===============================
# Search / Lists
# ===============================

async def find_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    if not context.args:
        return await update.message.reply_text("שימוש: /find_user <user_id>")

    user = sheets_service.get_supporter_by_id(context.args[0])
    await update.message.reply_text(str(user) if user else "לא נמצא.")


async def find_expert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    if not context.args:
        return await update.message.reply_text("שימוש: /find_expert <user_id>")

    expert = sheets_service.get_expert_by_id(context.args[0])
    await update.message.reply_text(str(expert) if expert else "לא נמצא.")


async def find_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    if not context.args:
        return await update.message.reply_text("שימוש: /find_position <id>")

    pos = sheets_service.get_position(context.args[0])
    await update.message.reply_text(str(pos) if pos else "לא נמצא.")


async def list_approved_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    experts = sheets_service.get_experts_leaderboard()
    approved = [e for e in experts if e.get("status") == "approved"]

    text = "מומחים מאושרים:\n"
    for e in approved:
        text += f"- {e.get('expert_full_name')} (מקום {e.get('expert_position')})\n"

    await update.message.reply_text(text)


async def list_rejected_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    experts = sheets_service.get_experts_leaderboard()
    rejected = [e for e in experts if e.get("status") == "rejected"]

    text = "מומחים שנדחו:\n"
    for e in rejected:
        text += f"- {e.get('expert_full_name')}\n"

    await update.message.reply_text(text)


async def list_supporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    users = sheets_service.get_users_sheet().get_all_records()
    text = "תומכים:\n"
    for u in users:
        text += f"- {u.get('full_name_telegram')} ({u.get('user_id')})\n"

    await update.message.reply_text(text)


# ===============================
# Broadcast
# ===============================

async def broadcast_supporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    if not context.args:
        return await update.message.reply_text("שימוש: /broadcast_supporters <טקסט>")

    text = " ".join(context.args)
    users = sheets_service.get_users_sheet().get_all_records()

    count = 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=int(u["user_id"]), text=text)
            count += 1
        except Exception:
            pass

    await update.message.reply_text(f"הודעה נשלחה ל-{count} תומכים.")


async def broadcast_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    if not context.args:
        return await update.message.reply_text("שימוש: /broadcast_experts <טקסט>")

    text = " ".join(context.args)
    experts = sheets_service.get_experts_sheet().get_all_records()

    count = 0
    for e in experts:
        try:
            await context.bot.send_message(chat_id=int(e["user_id"]), text=text)
            count += 1
        except Exception:
            pass

    await update.message.reply_text(f"הודעה נשלחה ל-{count} מומחים.")


# ===============================
# Monitoring
# ===============================

from bot.core.monitoring import monitoring

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("אין הרשאה.")

    m = monitoring.metrics
    text = (
        "Dashboard:\n"
        f"Total users: {m.total_users}\n"
        f"Messages today: {m.messages_today}\n"
        f"Errors: {m.errors}\n"
        f"Extra: {m.extra}\n"
    )
    await update.message.reply_text(text)


async def hourly_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("סטטיסטיקות לפי שעה אינן זמינות בגרסה זו.")


async def export_metrics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ייצוא מטריקות לא נתמך בגרסה זו.")


# ===============================
# Pagination (placeholder)
# ===============================

async def handle_experts_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("עמוד מומחים נוסף (placeholder).")


async def handle_supporters_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("עמוד תומכים נוסף (placeholder).")


# ===============================
# Admin menu callback fallback
# ===============================

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("תפריט אדמין:")


async def handle_admin_callback(query, context):
    await query.message.reply_text("פקודת אדמין לא מזוהה.")
