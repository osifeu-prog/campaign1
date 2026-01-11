import os
import time
import json
import traceback
from typing import Optional, List, Dict, Any
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services import sheets_service
from services import logger_service
from utils.constants import ADMIN_IDS, USERS_SHEET_NAME, EXPERTS_SHEET_NAME, POSITIONS_SHEET_NAME, LOG_GROUP_ID
from bot.core.monitoring import monitoring

# Safe Imports for Google API - Fixes the "No module named googleapiclient" error
try:
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials as GCreds
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False

# Helper: check admin
def _is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS

# -------------------------
# New: Quick Stats Command
# -------------------------
async def quick_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await (update.message.reply_text("אין לך הרשאה.") if update.message else None)
        return

    # handle both command and callback
    target = update.message if update.message else update.callback_query.message
    msg = await target.reply_text("⏳ מחשב נתונים בזמן אמת...")
    
    try:
        users_sheet = sheets_service.get_users_sheet()
        experts_sheet = sheets_service.get_experts_sheet()
        positions = sheets_service.get_positions()
        
        all_users = users_sheet.get_all_records()
        all_experts = experts_sheet.get_all_records()
        
        approved = sum(1 for r in all_experts if str(r.get("status", "")).lower() == "approved")
        pending = sum(1 for r in all_experts if str(r.get("status", "")).lower() == "pending")
        assigned_pos = sum(1 for p in positions if p.get('expert_user_id'))

        text = (
            "📊 **סטטיסטיקה מעודכנת:**\n\n"
            f"👤 **סה\"כ רשומים:** `{len(all_users)}` משתמשים\n"
            f"✅ **מומחים מאושרים:** `{approved}`\n"
            f"⏳ **בהמתנה לאישור:** `{pending}`\n"
            f"🏗️ **פוזיציות מאוישות:** `{assigned_pos}` מתוך `{len(positions)}`"
        )
        await msg.edit_text(text, parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ שגיאה בהפקת נתונים: {e}")

# -------------------------
# Positions commands
# -------------------------
async def list_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    
    positions = sheets_service.get_positions()
    if not positions:
        await (update.message.reply_text("אין מקומות מוגדרים.") if update.message else update.callback_query.message.reply_text("אין מקומות מוגדרים."))
        return
    
    text = "📍 **רשימת מקומות:**\n"
    for p in positions[:40]: # limit to avoid telegram message limit
        text += f"- {p.get('position_id')} : {p.get('expert_user_id') or 'פנוי'}\n"
    
    if update.message:
        await update.message.reply_text(text)
    else:
        await update.callback_query.message.reply_text(text)

async def position_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
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
    if not _is_admin(user.id): return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("שימוש: /assign <position_id> <user_id>")
        return
    pid, uid = args[0], args[1]
    sheets_service.assign_position(pid, uid, timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    await update.message.reply_text(f"המקום {pid} שוייך ל־{uid}.")

async def reset_position_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    args = context.args or []
    if not args:
        await update.message.reply_text("שימוש: /reset_position <position_id>")
        return
    pid = args[0]
    ok = sheets_service.reset_position(pid)
    await update.message.reply_text("איפוס בוצע." if ok else "מקום לא נמצא.")

async def reset_all_positions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    sheets_service.reset_all_positions()
    msg = "כל המקומות אופסו בהצלחה."
    await (update.message.reply_text(msg) if update.message else update.callback_query.message.reply_text(msg))

# -------------------------
# Sheets admin
# -------------------------
async def fix_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    sheets_service.auto_fix_all_sheets()
    msg = "תיקון גיליונות (Headers) הושלם."
    await (update.message.reply_text(msg) if update.message else update.callback_query.message.reply_text(msg))

async def validate_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    sheets_service.validate_all_sheets()
    await update.message.reply_text("ולידציה הושלמה.")

async def sheet_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    users = sheets_service.get_users_sheet()
    experts = sheets_service.get_experts_sheet()
    positions = sheets_service.get_positions_sheet()
    info = {
        "Users": sheets_service.get_sheet_info(users),
        "Experts": sheets_service.get_sheet_info(experts),
        "Positions": sheets_service.get_sheet_info(positions),
    }
    text = "📂 **מידע על הגיליונות:**\n" + json.dumps(info, ensure_ascii=False, indent=2)
    await (update.message.reply_text(text) if update.message else update.callback_query.message.reply_text(text))

async def clear_expert_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    deleted = sheets_service.clear_expert_duplicates()
    await (update.message.reply_text(f"הוסרו {deleted} כפילויות מומחים.") if update.message else update.callback_query.message.reply_text(f"הוסרו {deleted} כפילויות מומחים."))

async def clear_user_duplicates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    deleted = sheets_service.clear_user_duplicates()
    await (update.message.reply_text(f"הוסרו {deleted} כפילויות משתמשים.") if update.message else update.callback_query.message.reply_text(f"הוסרו {deleted} כפילויות משתמשים."))

# -------------------------
# Search / lists
# -------------------------
async def find_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
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
    if not _is_admin(user.id): return
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
    if not _is_admin(user.id): return
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
    text = "✅ **מומחים מאושרים:**\n" + "\n".join([f"{r.get('expert_full_name')} (id={r.get('user_id')})" for r in approved[:50]])
    await (update.message.reply_text(text or "אין מומחים מאושרים.") if update.message else update.callback_query.message.reply_text(text or "אין מומחים מאושרים."))

async def list_rejected_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sheets_service.get_experts_leaderboard()
    rejected = [r for r in rows if str(r.get("status", "")).lower() == "rejected"]
    text = "❌ **מומחים נדחים:**\n" + "\n".join([f"{r.get('expert_full_name')} (id={r.get('user_id')})" for r in rejected[:50]])
    await (update.message.reply_text(text or "אין מומחים נדחים.") if update.message else update.callback_query.message.reply_text(text or "אין מומחים נדחים."))

async def list_supporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = sheets_service.get_users_sheet()
    rows = sheet.get_all_records()
    text = f"👥 מספר תומכים רשומים: {len(rows)}"
    await (update.message.reply_text(text) if update.message else update.callback_query.message.reply_text(text))

# -------------------------
# Unified Admin Menu
# -------------------------
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("אין לך הרשאה.")
        return

    keyboard = [
        [
            InlineKeyboardButton("📊 סטטיסטיקה", callback_data="admin_stats_quick"),
            InlineKeyboardButton("📈 דאשבורד", callback_data="admin_dashboard")
        ],
        [
            InlineKeyboardButton("📂 מידע גיליונות", callback_data="admin_sheets_info"),
            InlineKeyboardButton("💾 גיבוי עכשיו", callback_data="admin_run_backup")
        ],
        [
            InlineKeyboardButton("🛠️ תיקון גיליונות", callback_data="admin_sheets_fix"),
            InlineKeyboardButton("🧹 ניקוי כפילויות", callback_data="admin_clear_dups")
        ],
        [
            InlineKeyboardButton("✅ מומחים מאושרים", callback_data="admin_list_approved"),
            InlineKeyboardButton("❌ מומחים שנדחו", callback_data="admin_list_rejected")
        ],
        [
            InlineKeyboardButton("🏗️ רשימת פוזיציות", callback_data="admin_list_positions"),
            InlineKeyboardButton("🔄 איפוס פוזיציות", callback_data="admin_reset_all_pos")
        ],
        [
            InlineKeyboardButton("📢 שידור לתומכים", callback_data="admin_broadcast_supporters")
        ]
    ]
    
    admin_text = "👑 **לוח בקרת מנהל - הכל במקום אחד**\nבחר פעולה לבדיקת תקינות המערכת:"
    
    if update.message:
        await update.message.reply_text(admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def expert_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    await query.answer()
    
    # Menu Navigation
    if data == "admin_stats_quick":
        await quick_stats_command(update, context)
    elif data == "admin_dashboard":
        await dashboard_command(update, context)
    elif data == "admin_sheets_info":
        await sheet_info(update, context)
    elif data == "admin_run_backup":
        await backup_sheets_cmd(update, context)
    elif data == "admin_sheets_fix":
        await fix_sheets(update, context)
    elif data == "admin_clear_dups":
        await clear_user_duplicates_cmd(update, context)
        await clear_expert_duplicates_cmd(update, context)
    elif data == "admin_list_approved":
        await list_approved_experts(update, context)
    elif data == "admin_list_rejected":
        await list_rejected_experts(update, context)
    elif data == "admin_list_positions":
        await list_positions(update, context)
    elif data == "admin_reset_all_pos":
        await reset_all_positions_cmd(update, context)
    elif data == "admin_broadcast_supporters":
        await query.message.reply_text("להפעלת שידור השתמש ב: `/broadcast_supporters <text>`")

    # Original Expert Approval Logic
    elif data.startswith("expert_approve:"):
        uid = data.split(":", 1)[1]
        ok = sheets_service.update_expert_status(uid, "approved")
        if ok:
            await query.edit_message_text(f"✅ מומחה {uid} אושר.")
            await logger_service.log(context, "Expert approved", user=update.effective_user, extra={"EXPERT_USER_ID": uid})
        else:
            await query.edit_message_text("❌ שגיאה באישור.")
    elif data.startswith("expert_reject:"):
        uid = data.split(":", 1)[1]
        ok = sheets_service.update_expert_status(uid, "rejected")
        if ok:
            await query.edit_message_text(f"❌ מומחה {uid} נדחה.")
            await logger_service.log(context, "Expert rejected", user=update.effective_user, extra={"EXPERT_USER_ID": uid})
        else:
            await query.edit_message_text("❌ שגיאה בדחייה.")

# -------------------------
# Broadcasts
# -------------------------
async def broadcast_supporters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("שימוש: /broadcast_supporters <text>")
        return
    sheet = sheets_service.get_users_sheet()
    rows = sheet.get_all_records()
    count = 0
    for r in rows:
        try:
            await context.bot.send_message(chat_id=int(r.get("user_id")), text=text)
            count += 1
        except: continue
    await update.message.reply_text(f"שודרו {count} הודעות.")

async def broadcast_experts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("שימוש: /broadcast_experts <text>")
        return
    sheet = sheets_service.get_experts_sheet()
    rows = sheet.get_all_records()
    count = 0
    for r in rows:
        try:
            await context.bot.send_message(chat_id=int(r.get("user_id")), text=text)
            count += 1
        except: continue
    await update.message.reply_text(f"שודרו {count} הודעות.")

# -------------------------
# Monitoring / Dashboard
# -------------------------
async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    metrics = monitoring.metrics
    text = f"📈 **דאשבורד מערכת:**\nסה\"כ משתמשים: {metrics.total_users}\nהודעות היום: {metrics.messages_today}"
    await (update.message.reply_text(text) if update.message else update.callback_query.message.reply_text(text))

async def hourly_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hourly stats: (לא הוטמע)")

async def export_metrics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Export metrics: (לא הוטמע)")

# -------------------------
# Pagination / Leaderboard
# -------------------------
async def handle_experts_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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
    text = "🏆 **Leaderboard:**\n"
    for r in rows[:10]:
        text += f"{r.get('expert_full_name')} — {r.get('supporters_count', 0)} supporters\n"
    await update.message.reply_text(text)

# -------------------------
# Backup sheets (Drive API)
# -------------------------
async def backup_sheets_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id): return
    
    # handling both command and callback
    target = update.message if update.message else update.callback_query.message
        
    if not HAS_GOOGLE_API:
        await target.reply_text("❌ ספריות Google API חסרות.")
        return

    status_msg = await target.reply_text("🔄 יוצר גיבוי...")
    try:
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
        info = json.loads(creds_json) if creds_json.startswith('{') else json.load(open(creds_json))
        credentials = GCreds.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/drive"])
        drive_service = build("drive", "v3", credentials=credentials)

        spreadsheet_id = sheets_service.SPREADSHEET_ID
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        body = {"name": f"Backup_Campaign1_{timestamp}"}
        
        copied = drive_service.files().copy(fileId=spreadsheet_id, body=body).execute()
        link = f"https://docs.google.com/spreadsheets/d/{copied.get('id')}"
        await status_msg.edit_text(f"✅ גיבוי נוצר!\nלינק: {link}")
    except Exception as e:
        await status_msg.edit_text(f"❌ שגיאה: {e}")

# Export list
__all__ = [
    "list_positions", "position_details", "assign_position_cmd", "reset_position_cmd",
    "reset_all_positions_cmd", "fix_sheets", "validate_sheets", "sheet_info",
    "clear_expert_duplicates_cmd", "clear_user_duplicates_cmd", "find_user",
    "find_expert", "find_position", "list_approved_experts", "list_rejected_experts",
    "list_supporters", "admin_menu", "expert_admin_callback", "broadcast_supporters",
    "broadcast_experts", "dashboard_command", "hourly_stats_command", "export_metrics_command",
    "handle_experts_pagination", "handle_supporters_pagination", "leaderboard_command",
    "backup_sheets_cmd", "quick_stats_command",
]
