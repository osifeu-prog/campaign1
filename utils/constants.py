# utils/constants.py
# קובץ קבועים מרכזי לפרויקט Campaign1
import os
import sys
from typing import List

# ===============================
# ENV בסיסיים
# ===============================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")

# ===============================
# Google Sheets - שמות גיליונות (ברירת מחדל)
# ===============================
USERS_SHEET_NAME = os.getenv("USERS_SHEET_NAME", "Users")
EXPERTS_SHEET_NAME = os.getenv("EXPERTS_SHEET_NAME", "Experts")
POSITIONS_SHEET_NAME = os.getenv("POSITIONS_SHEET_NAME", "Positions")

# ===============================
# Telegram Groups / IDs
# ===============================
LOG_GROUP_ID = os.getenv("LOG_GROUP_ID", "")
SUPPORT_GROUP_ID = os.getenv("SUPPORT_GROUP_ID", "")
EXPERTS_GROUP_ID = os.getenv("EXPERTS_GROUP_ID", "")
ACTIVISTS_GROUP_ID = os.getenv("ACTIVISTS_GROUP_ID", "")
ALL_MEMBERS_GROUP_ID = os.getenv("ALL_MEMBERS_GROUP_ID", "")

# ===============================
# ADMIN_IDS - ולידציה
# ===============================
def _parse_admin_ids(raw: str) -> List[str]:
    if not raw or not raw.strip():
        return []
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts

_ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = _parse_admin_ids(_ADMIN_IDS_RAW)

# אם רוצים להכריח ADMIN_IDS, אפשר להפעיל ולידציה נוקשה:
# אם אין ADMIN_IDS מוגדרים, לא נזרוק שגיאה אוטומטית כאן כדי לא לחסום deploy,
# אך נוכל להדפיס אזהרה.
if not ADMIN_IDS:
    print("⚠️ Warning: ADMIN_IDS is empty. Some admin-only commands will be unavailable.", file=sys.stderr)

# ===============================
# TON / Donations
# ===============================
TON_WALLET_ADDRESS = os.getenv("TON_WALLET_ADDRESS", "")
try:
    MIN_DONATION_AMOUNT = float(os.getenv("MIN_DONATION_AMOUNT", "1"))
except Exception:
    MIN_DONATION_AMOUNT = 1.0

# ===============================
# תמונות / משאבים
# ===============================
# נתיב יחסי לתיקיית assets (אם קיימת)
START_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "media", "start_slides")

# ===============================
# Roles / תפקידים
# ===============================
ROLE_SUPPORTER = "supporter"
ROLE_EXPERT = "expert"
ROLE_ACTIVIST = "activist"

# ===============================
# הגדרות כלליות
# ===============================
try:
    MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "20"))
except Exception:
    MAX_POSITIONS = 20

DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")

# ===============================
# Callback Data keys
# ===============================
# Start carousel
CALLBACK_START_SLIDE = "start_slide"
CALLBACK_START_SOCI = "start_soci"
CALLBACK_START_FINISH = "start_finish"

# Main menu
CALLBACK_MENU_MAIN = "menu_main"
CALLBACK_MENU_SUPPORT = "menu_support"
CALLBACK_MENU_EXPERT = "menu_expert"
CALLBACK_MENU_ADMIN = "menu_admin"
CALLBACK_MENU_POSITIONS = "menu_positions"

# Apply flows
CALLBACK_APPLY_SUPPORTER = "apply_supporter"
CALLBACK_APPLY_EXPERT = "apply_expert"

# Admin sheets
CALLBACK_ADMIN_SHEETS = "admin_sheets"
CALLBACK_ADMIN_SHEETS_INFO = "admin_sheets_info"
CALLBACK_ADMIN_SHEETS_FIX = "admin_sheets_fix"
CALLBACK_ADMIN_SHEETS_VALIDATE = "admin_sheets_validate"
CALLBACK_ADMIN_SHEETS_CLEAR_DUP = "admin_sheets_clear_dup"
CALLBACK_ADMIN_BROADCAST = "admin_broadcast"
CALLBACK_ADMIN_EXPORT = "admin_export"
CALLBACK_ADMIN_QUICK_NAV = "admin_quick_nav"

# Donations
CALLBACK_DONATE = "donate"
CALLBACK_DONATE_CUSTOM = "donate_custom"
# Donation helper callbacks (copy / info)
CALLBACK_COPY_WALLET = "copy_wallet"
CALLBACK_TON_INFO = "ton_info"

# Leaderboard / Expert profile
CALLBACK_LEADERBOARD = "leaderboard"
CALLBACK_EXPERT_PROFILE = "expert_profile"  # used as prefix: expert_profile:<user_id>

# Help
CALLBACK_HELP_INFO = "help_info"

# Pagination prefixes
CALLBACK_EXPERTS_PAGE = "experts_page"
CALLBACK_SUPPORTERS_PAGE = "supporters_page"

# Expert admin actions (patterns handled elsewhere)
CALLBACK_EXPERT_APPROVE = "expert_approve"
CALLBACK_EXPERT_REJECT = "expert_reject"

# ===============================
# Export / Misc
# ===============================
# Default values for other features
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "10"))

# ===============================
# Export list
# ===============================
__all__ = [
    "TELEGRAM_BOT_TOKEN",
    "WEBHOOK_URL",
    "GOOGLE_SHEETS_SPREADSHEET_ID",
    "GOOGLE_CREDENTIALS_JSON",
    "USERS_SHEET_NAME",
    "EXPERTS_SHEET_NAME",
    "POSITIONS_SHEET_NAME",
    "LOG_GROUP_ID",
    "SUPPORT_GROUP_ID",
    "EXPERTS_GROUP_ID",
    "ACTIVISTS_GROUP_ID",
    "ALL_MEMBERS_GROUP_ID",
    "ADMIN_IDS",
    "TON_WALLET_ADDRESS",
    "MIN_DONATION_AMOUNT",
    "START_IMAGES_DIR",
    "ROLE_SUPPORTER",
    "ROLE_EXPERT",
    "ROLE_ACTIVIST",
    "MAX_POSITIONS",
    "DEFAULT_TIMEZONE",
    "CALLBACK_START_SLIDE",
    "CALLBACK_START_SOCI",
    "CALLBACK_START_FINISH",
    "CALLBACK_MENU_MAIN",
    "CALLBACK_MENU_SUPPORT",
    "CALLBACK_MENU_EXPERT",
    "CALLBACK_MENU_ADMIN",
    "CALLBACK_MENU_POSITIONS",
    "CALLBACK_APPLY_SUPPORTER",
    "CALLBACK_APPLY_EXPERT",
    "CALLBACK_ADMIN_SHEETS",
    "CALLBACK_ADMIN_SHEETS_INFO",
    "CALLBACK_ADMIN_SHEETS_FIX",
    "CALLBACK_ADMIN_SHEETS_VALIDATE",
    "CALLBACK_ADMIN_SHEETS_CLEAR_DUP",
    "CALLBACK_ADMIN_BROADCAST",
    "CALLBACK_ADMIN_EXPORT",
    "CALLBACK_ADMIN_QUICK_NAV",
    "CALLBACK_DONATE",
    "CALLBACK_DONATE_CUSTOM",
    "CALLBACK_COPY_WALLET",
    "CALLBACK_TON_INFO",
    "CALLBACK_LEADERBOARD",
    "CALLBACK_EXPERT_PROFILE",
    "CALLBACK_HELP_INFO",
    "CALLBACK_EXPERTS_PAGE",
    "CALLBACK_SUPPORTERS_PAGE",
    "CALLBACK_EXPERT_APPROVE",
    "CALLBACK_EXPERT_REJECT",
    "DEFAULT_PAGE_SIZE",
]
# --- image / media settings ---
# רשימת רזולוציות לבקשתך (width, height)
IMAGE_SIZES = [(320, 180), (640, 360), (960, 540)]

# תיקיית זמנית לשמירת מדיה לעיבוד
TEMP_MEDIA_DIR = os.getenv("TEMP_MEDIA_DIR", "/tmp/campaign1_media")

# מגבלות לעיבוד GIF/מדיה
try:
    MAX_GIF_DURATION_SECONDS = int(os.getenv("MAX_GIF_DURATION_SECONDS", "10"))
except Exception:
    MAX_GIF_DURATION_SECONDS = 10

try:
    MAX_MEDIA_FILESIZE_MB = int(os.getenv("MAX_MEDIA_FILESIZE_MB", "20"))
except Exception:
    MAX_MEDIA_FILESIZE_MB = 20
