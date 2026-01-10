# ===============================
# קבועים גלובליים מהסביבה (ENV)
# ===============================

import os

# מזהי אדמינים (רשימת user_id כמחרוזות, מופרדים בפסיק ב־ENV)
ADMIN_IDS = [i for i in os.getenv("ADMIN_IDS", "").split(",") if i]

# קבוצות
LOG_GROUP_ID = os.getenv("LOG_GROUP_ID", "")
ALL_MEMBERS_GROUP_ID = os.getenv("ALL_MEMBERS_GROUP_ID", "")
ACTIVISTS_GROUP_ID = os.getenv("ACTIVISTS_GROUP_ID", "")
EXPERTS_GROUP_ID = os.getenv("EXPERTS_GROUP_ID", "")
SUPPORT_GROUP_ID = os.getenv("SUPPORT_GROUP_ID", "")

# תפקידי משתמשים
ROLE_SUPPORTER = "supporter"
ROLE_EXPERT = "expert"

# מספר מקומות
MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "121"))

# תיקיית תמונות לפתיחת /start
START_IMAGES_DIR = os.getenv("START_IMAGES_DIR", "media/start_slides")

# callback data קבועים לתפריטים
CALLBACK_MENU_MAIN = "menu_main"
CALLBACK_MENU_SUPPORT = "menu_support"
CALLBACK_MENU_EXPERT = "menu_expert"
CALLBACK_MENU_ADMIN = "menu_admin"

CALLBACK_APPLY_EXPERT = "apply_expert_again"
CALLBACK_APPLY_SUPPORTER = "apply_supporter"

CALLBACK_ADMIN_PENDING_EXPERTS = "admin_pending_experts"
CALLBACK_ADMIN_GROUPS = "admin_groups"

CALLBACK_ADMIN_SHEETS = "admin_sheets"
CALLBACK_ADMIN_SHEETS_INFO = "admin_sheets_info"
CALLBACK_ADMIN_SHEETS_FIX = "admin_sheets_fix"
CALLBACK_ADMIN_SHEETS_VALIDATE = "admin_sheets_validate"
CALLBACK_ADMIN_SHEETS_CLEAR_DUP = "admin_sheets_clear_dup"

CALLBACK_ADMIN_BROADCAST = "admin_broadcast"
CALLBACK_ADMIN_EXPORT = "admin_export"
CALLBACK_ADMIN_QUICK_NAV = "admin_quick_nav"

CALLBACK_MENU_POSITIONS = "menu_positions"

# קרוסלת פתיחה /start
CALLBACK_START_SLIDE = "start_slide"          # start_slide:<index>
CALLBACK_START_SOCI = "start_sociocracy"      # מסך הסוציוקרטיה
CALLBACK_START_SOCI_BACK = "start_soci_back"  # חזרה מהסוציוקרטיה לקרוסלה
CALLBACK_START_FINISH = "start_finish"        # מעבר למסך "ברוך הבא"
