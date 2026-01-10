# ===============================
# utils/constants.py - קבועים משודרגים
# ===============================

import os
import sys

# ===============================
# Google Sheets
# ===============================

USERS_SHEET_NAME = os.getenv("USERS_SHEET_NAME", "Users")
EXPERTS_SHEET_NAME = os.getenv("EXPERTS_SHEET_NAME", "Experts")
POSITIONS_SHEET_NAME = os.getenv("POSITIONS_SHEET_NAME", "Positions")

# ===============================
# Telegram Groups
# ===============================

LOG_GROUP_ID = os.getenv("LOG_GROUP_ID")
SUPPORT_GROUP_ID = os.getenv("SUPPORT_GROUP_ID")
EXPERTS_GROUP_ID = os.getenv("EXPERTS_GROUP_ID")
ACTIVISTS_GROUP_ID = os.getenv("ACTIVISTS_GROUP_ID")
ALL_MEMBERS_GROUP_ID = os.getenv("ALL_MEMBERS_GROUP_ID")

# ===============================
# Admin IDs - עם ולידציה
# ===============================

def validate_admin_ids():
    """
    ולידציה בטוחה של ADMIN_IDS
    """
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    
    if not admin_ids_str or not admin_ids_str.strip():
        print("❌ ERROR: ADMIN_IDS cannot be empty", file=sys.stderr)
        raise SystemExit(1)
    
    ids = [id_str.strip() for id_str in admin_ids_str.split(",")]
    
    # בדיקה שכל המזהים הם מספרים
    for id_str in ids:
        if not id_str.isdigit():
            print(f"❌ ERROR: Invalid admin ID: {id_str}", file=sys.stderr)
            raise SystemExit(1)
    
    if len(ids) == 0:
        print("❌ ERROR: At least one admin ID is required", file=sys.stderr)
        raise SystemExit(1)
    
    return ids

ADMIN_IDS = validate_admin_ids()

# ===============================
# TON Wallet
# ===============================

TON_WALLET_ADDRESS = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
MIN_DONATION_AMOUNT = 1.0  # TON

# ===============================
# תמונות
# ===============================

START_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "images")

# ===============================
# תפקידים
# ===============================

ROLE_SUPPORTER = "supporter"
ROLE_EXPERT = "expert"
ROLE_ACTIVIST = "activist"

# ===============================
# מקומות
# ===============================

MAX_POSITIONS = 120

# ===============================
# Callback Data
# ===============================

# תפריטים ראשיים
CALLBACK_MENU_MAIN = "menu_main"
CALLBACK_MENU_SUPPORT = "menu_support"
CALLBACK_MENU_EXPERT = "menu_expert"
CALLBACK_MENU_ADMIN = "menu_admin"
CALLBACK_MENU_POSITIONS = "menu_positions"

# הרשמות
CALLBACK_APPLY_SUPPORTER = "apply_supporter"
CALLBACK_APPLY_EXPERT = "apply_expert"

# תפריטי אדמין
CALLBACK_ADMIN_SHEETS = "admin_sheets"
CALLBACK_ADMIN_SHEETS_INFO = "admin_sheets_info"
CALLBACK_ADMIN_SHEETS_FIX = "admin_sheets_fix"
CALLBACK_ADMIN_SHEETS_VALIDATE = "admin_sheets_validate"
CALLBACK_ADMIN_SHEETS_CLEAR_DUP = "admin_sheets_clear_dup"
CALLBACK_ADMIN_BROADCAST = "admin_broadcast"
CALLBACK_ADMIN_EXPORT = "admin_export"
CALLBACK_ADMIN_QUICK_NAV = "admin_quick_nav"

# קרוסלת start
CALLBACK_START_SLIDE = "start_slide"
CALLBACK_START_SOCI = "start_soci"
CALLBACK_START_FINISH = "start_finish"

# תרומות - חדש
CALLBACK_DONATE = "donate"
CALLBACK_DONATE_CUSTOM = "donate_custom"

# Leaderboard - חדש
CALLBACK_LEADERBOARD = "leaderboard"
CALLBACK_EXPERT_PROFILE = "expert_profile"
