# bot/handlers/admin_handlers.py
import os
import time
import json
from typing import Optional, List, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services import sheets_service
from services import logger_service
from utils.constants import ADMIN_IDS, USERS_SHEET_NAME, EXPERTS_SHEET_NAME, POSITIONS_SHEET_NAME, LOG_GROUP_ID
from bot.core.monitoring import monitoring

# Helper: check admin
def _is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS

# -------------------------
# Positions commands
# -------------------------
async def list_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה להריץ פקודה זו.")
        return
    positions = sheets_service.get_positions()
    if not positions:
        await update.message.reply_text("אין מקומות מוגדרים.")
        return
    text = "רשימת מקומות:\n"
    for p in positions:
        text += f"- {p.get('position_id')} : assigned_to={p.get('expert_user_id') or 'free'}\n"
    await update.message.reply_text(text)

async def position_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה להריץ פקודה זו.")
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("יש לציין מספר מקום: /position <id>")
        return
    pid = args[0]
    pos = sheets_service.get_position(pid)
    if not pos:
        await update.message.reply_text("מקום לא נמצא.")
        return
    await update.message.reply_text(json.dumps(pos, ensure_ascii=False, indent=2))

async def assign_position_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("שימוש: /assign <position_id> <user_id>")
        return
    pid, uid = args[0], args[1]
    sheets_service.assign_position(pid, uid, timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    await update.message.reply_text(f"המקום {pid} שוייך ל־{uid}.")

async def reset_position_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("שימוש: /reset_position <position_id>")
        return
    pid = args[0]
    ok = sheets_service.reset_position(pid)
    await update.message.reply_text("איפוס בוצע." if ok else "מקום לא נמצא.")

async def reset_all_positions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    sheets_service.reset_all_positions()
    await update.message.reply_text("כל המקומות אופסו.")

# -------------------------
# Sheets admin
# -------------------------
async def fix_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    sheets_service.auto_fix_all_sheets()
    await update.message.reply_text("תיקון גיליונות הושלם.")

async def validate_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    sheets_service.validate_all_sheets()
    await update.message.reply_text("ולידציה הושלמה.")

async def sheet_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    # show basic info for main sheets
    users = sheets_service.get_users_sheet()
    experts = sheets_service.get_experts_sheet()
    positions = sheets_service.get_positions_sheet()
    info = {
        "Users": sheets_service.get_sheet_info(users),
        "Experts": sheets_service.get_sheet_info(experts),
        "Positions": sheets_service.get_sheet_info(positions),
    }
    await update.message.reply_text(json.dumps(info, ensure_ascii=False, indent=2))

async def clear_expert_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    deleted = sheets_service.clear_expert_duplicates()
    await update.message.reply_text(f"הוסרו {deleted} כפילויות מומחים.")

async def clear_user_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    deleted = sheets_service.clear_user_duplicates()
    await update.message.reply_text(f"הוסרו {deleted} כפילויות משתמשים.")

# -------------------------
# Search / lists
# -------------------------
async def find_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("שימוש: /find_user <user_id>")
        return
    uid = args[0]
    rec = sheets_service.get_supporter_by_id(uid)
    if not rec:
        await update.message.reply_text("משתמש לא נמצא.")
        return
    await update.message.reply_text(json.dumps(rec, ensure_ascii=False, indent=2))

async def find_expert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("שימוש: /find_expert <user_id>")
        return
    uid = args[0]
    rec = sheets_service.get_expert_by_id(uid)
    if not rec:
        await update.message.reply_text("מומחה לא נמצא.")
        return
    await update.message.reply_text(json.dumps(rec, ensure_ascii=False, indent=2))

async def find_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("שימוש: /find_position <position_id>")
        return
    pid = args[0]
    rec = sheets_service.get_position(pid)
    if not rec:
        await update.message.reply_text("מקום לא נמצא.")
        return
    await update.message.reply_text(json.dumps(rec, ensure_ascii=False, indent=2))

async def list_approved_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sheets_service.get_experts_leaderboard()
    approved = [r for r in rows if str(r.get("status", "")).lower() == "approved"]
    text = "מומחים מאושרים:\n" + "\n".join([f"{r.get('expert_full_name')} (id={r.get('user_id')})" for r in approved[:50]])
    await update.message.reply_text(text or "אין מומחים מאושרים.")

async def list_rejected_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sheets_service.get_experts_leaderboard()
    rejected = [r for r in rows if str(r.get("status", "")).lower() == "rejected"]
    text = "מומחים נדחים:\n" + "\n".join([f"{r.get('expert_full_name')} (id={r.get('user_id')})" for r in rejected[:50]])
    await update.message.reply_text(text or "אין מומחים נדחים.")

async def list_supporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = sheets_service.get_users_sheet()
    rows = sheet.get_all_records()
    text = f"מספר תומכים: {len(rows)}"
    await update.message.reply_text(text)

# -------------------------
# Admin menu / callbacks
# -------------------------
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה לפתוח את תפריט האדמין.")
        return
    kb = [
        [InlineKeyboardButton("מידע על גיליונות", callback_data="admin_sheets_info")],
        [InlineKeyboardButton("תיקון גיליונות", callback_data="admin_sheets_fix")],
        [InlineKeyboardButton("שידור לתומכים", callback_data="admin_broadcast_supporters")],
    ]
    await update.message.reply_text("תפריט אדמין:", reply_markup=InlineKeyboardMarkup(kb))

async def expert_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles callback queries for expert approval/rejection.
    Expected callback_data: expert_approve:<user_id> or expert_reject:<user_id>
    """
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data.startswith("expert_approve:"):
        uid = data.split(":", 1)[1]
        ok = sheets_service.update_expert_status(uid, "approved")
        if ok:
            await query.edit_message_text("מומחה אושר.")
            await logger_service.log(context, "Expert approved", user=update.effective_user, extra={"EXPERT_USER_ID": uid})
        else:
            await query.edit_message_text("שגיאה באישור מומחה.")
    elif data.startswith("expert_reject:"):
        uid = data.split(":", 1)[1]
        ok = sheets_service.update_expert_status(uid, "rejected")
        if ok:
            await query.edit_message_text("מומחה נדחה.")
            await logger_service.log(context, "Expert rejected", user=update.effective_user, extra={"EXPERT_USER_ID": uid})
        else:
            await query.edit_message_text("שגיאה בדחיית מומחה.")
    else:
        await query.edit_message_text("פעולה לא מזוהה.")

# -------------------------
# Broadcasts
# -------------------------
async def broadcast_supporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    text = " ".join(context.args) if context.args else "שידור מנהל"
    sheet = sheets_service.get_users_sheet()
    rows = sheet.get_all_records()
    count = 0
    for r in rows:
        try:
            chat_id = int(r.get("user_id"))
            await context.bot.send_message(chat_id=chat_id, text=text)
            count += 1
        except Exception:
            continue
    await update.message.reply_text(f"שודרו הודעות ל־{count} תומכים.")

async def broadcast_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    text = " ".join(context.args) if context.args else "שידור מנהל למומחים"
    sheet = sheets_service.get_experts_sheet()
    rows = sheet.get_all_records()
    count = 0
    for r in rows:
        try:
            chat_id = int(r.get("user_id"))
            await context.bot.send_message(chat_id=chat_id, text=text)
            count += 1
        except Exception:
            continue
    await update.message.reply_text(f"שודרו הודעות ל־{count} מומחים.")

# -------------------------
# Monitoring / dashboard
# -------------------------
async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return
    metrics = monitoring.metrics
    text = f"Dashboard:\nTotal users: {metrics.total_users}\nMessages today: {metrics.messages_today}"
    await update.message.reply_text(text)

async def hourly_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hourly stats: (not implemented in detail)")

async def export_metrics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Export metrics: (not implemented)")

# -------------------------
# Pagination / leaderboard
# -------------------------
async def handle_experts_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # simple placeholder: show top 10
    rows = sheets_service.get_experts_leaderboard()
    text = "Leaderboard (top 10):\n"
    for r in rows[:10]:
        text += f"{r.get('expert_full_name')} — supporters: {r.get('supporters_count', 0)}\n"
    await query.edit_message_text(text)

async def handle_supporters_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sheet = sheets_service.get_users_sheet()
    rows = sheet.get_all_records()
    text = f"Supporters count: {len(rows)}"
    await query.edit_message_text(text)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sheets_service.get_experts_leaderboard()
    text = "Leaderboard:\n"
    for r in rows[:10]:
        text += f"{r.get('expert_full_name')} — {r.get('supporters_count', 0)} supporters\n"
    await update.message.reply_text(text)

# -------------------------
# Backup sheets (admin)
# -------------------------
async def backup_sheets_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה להריץ גיבוי.")
        return
    try:
        # load credentials info
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
        try:
            info = json.loads(creds_json)
        except Exception:
            with open(creds_json, "r", encoding="utf-8") as fh:
                info = json.load(fh)

        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials as GCreds

        scopes = ["https://www.googleapis.com/auth/drive"]
        credentials = GCreds.from_service_account_info(info, scopes=scopes)
        drive_service = build("drive", "v3", credentials=credentials)

        spreadsheet_id = sheets_service.SPREADSHEET_ID
        body = {"name": f"backup_{spreadsheet_id}_{int(time.time())}"}
        copied = drive_service.files().copy(fileId=spreadsheet_id, body=body).execute()
        copy_id = copied.get("id")
        # create share link (viewer) - optional
        drive_service.permissions().create(fileId=copy_id, body={"type":"anyone","role":"reader"}).execute()
        link = f"https://docs.google.com/spreadsheets/d/{copy_id}"
        await update.message.reply_text(f"גיבוי נוצר בהצלחה: {link}")
    except Exception as e:
        await update.message.reply_text(f"שגיאה ביצירת גיבוי: {e}")

# Export list for imports
__all__ = [
    "list_positions",
    "position_details",
    "assign_position_cmd",
    "reset_position_cmd",
    "reset_all_positions_cmd",
    "fix_sheets",
    "validate_sheets",
    "sheet_info",
    "clear_expert_duplicates_cmd",
    "clear_user_duplicates_cmd",
    "find_user",
    "find_expert",
    "find_position",
    "list_approved_experts",
    "list_rejected_experts",
    "list_supporters",
    "admin_menu",
    "expert_admin_callback",
    "broadcast_supporters",
    "broadcast_experts",
    "dashboard_command",
    "hourly_stats_command",
    "export_metrics_command",
    "handle_experts_pagination",
    "handle_supporters_pagination",
    "leaderboard_command",
    "backup_sheets_cmd",
]
