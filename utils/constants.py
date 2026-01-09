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

# callback data קבועים לתפריטים
CALLBACK_MENU_MAIN = "menu_main"
CALLBACK_MENU_SUPPORT = "menu_support"
CALLBACK_MENU_EXPERT = "menu_expert"
CALLBACK_MENU_ADMIN = "menu_admin"
CALLBACK_APPLY_EXPERT = "apply_expert_again"
CALLBACK_APPLY_SUPPORTER = "apply_supporter"
CALLBACK_ADMIN_PENDING_EXPERTS = "admin_pending_experts"
CALLBACK_ADMIN_GROUPS = "admin_groups"

CALLBACK_MENU_POSITIONS = "menu_positions"
