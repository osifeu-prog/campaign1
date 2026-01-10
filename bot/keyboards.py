# ===============================
# מקלדות (InlineKeyboardMarkup)
# ===============================

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from utils.constants import (
    CALLBACK_MENU_MAIN,
    CALLBACK_MENU_SUPPORT,
    CALLBACK_MENU_EXPERT,
    CALLBACK_MENU_ADMIN,
    CALLBACK_ADMIN_PENDING_EXPERTS,
    CALLBACK_ADMIN_GROUPS,
    CALLBACK_MENU_POSITIONS,
    CALLBACK_APPLY_EXPERT,
    CALLBACK_ADMIN_SHEETS,
    CALLBACK_ADMIN_BROADCAST,
    CALLBACK_ADMIN_EXPORT,
    CALLBACK_ADMIN_QUICK_NAV,
)


def build_main_menu_for_user(user_id: int, is_admin: bool) -> InlineKeyboardMarkup:
    """
    תפריט ראשי למשתמש: תומך / מומחה / אדמין
    """
    buttons = [
        [InlineKeyboardButton("🧑‍🎓 הרשמה / פרופיל תומך", callback_data=CALLBACK_MENU_SUPPORT)],
        [InlineKeyboardButton("🧠 פאנל מומחה", callback_data=CALLBACK_MENU_EXPERT)],
        [InlineKeyboardButton("📊 רשימת מקומות", callback_data=CALLBACK_MENU_POSITIONS)],
        [InlineKeyboardButton("🆘 תמיכה", callback_data=CALLBACK_MENU_SUPPORT)],
    ]

    if is_admin:
        buttons.append([InlineKeyboardButton("🛠️ פאנל אדמין", callback_data=CALLBACK_MENU_ADMIN)])

    return InlineKeyboardMarkup(buttons)


def build_start_keyboard() -> InlineKeyboardMarkup:
    """
    מקלדת למסך הפתיחה /start
    """
    buttons = [
        [
            InlineKeyboardButton("🧠 אני מומחה", callback_data="expert"),
            InlineKeyboardButton("🧑‍🎓 אני תומך", callback_data="supporter"),
        ],
        [InlineKeyboardButton("📋 פתח תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ]
    return InlineKeyboardMarkup(buttons)


def build_supporter_profile_keyboard(personal_link: str) -> InlineKeyboardMarkup:
    """
    מקלדת למסך 'פרופיל תומך'
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 לשתף את הקישור האישי", url=personal_link)],
        [InlineKeyboardButton("🧠 להגיש מועמדות כמומחה", callback_data=CALLBACK_MENU_EXPERT)],
        [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ])


def build_expert_panel_keyboard(status: str, referral_link: str | None) -> InlineKeyboardMarkup:
    """
    מקלדת למסך 'פאנל מומחה'
    """
    buttons: list[list[InlineKeyboardButton]] = []

    if status == "approved" and referral_link:
        buttons.append([InlineKeyboardButton("📣 לשתף את קישור המומחה", url=referral_link)])

    if status in ("rejected", "approved"):
        buttons.append([InlineKeyboardButton("🧠 הגשת מועמדות מחדש", callback_data=CALLBACK_APPLY_EXPERT)])

    buttons.append([InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)])

    return InlineKeyboardMarkup(buttons)


def build_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """
    מקלדת לפאנל אדמין ראשי
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧑‍⚖️ מומחים ממתינים", callback_data=CALLBACK_ADMIN_PENDING_EXPERTS)],
        [InlineKeyboardButton("📊 רשימת מקומות", callback_data=CALLBACK_MENU_POSITIONS)],
        [InlineKeyboardButton("🧩 ניהול קבוצות", callback_data=CALLBACK_ADMIN_GROUPS)],
        [InlineKeyboardButton("📊 ניהול גיליונות", callback_data=CALLBACK_ADMIN_SHEETS)],
        [InlineKeyboardButton("📨 שליחת הודעה לתומכים / מומחים", callback_data=CALLBACK_ADMIN_BROADCAST)],
        [InlineKeyboardButton("📁 יצוא נתונים (טקסט)", callback_data=CALLBACK_ADMIN_EXPORT)],
        [InlineKeyboardButton("🧭 ניווט מהיר", callback_data=CALLBACK_ADMIN_QUICK_NAV)],
        [InlineKeyboardButton("↩️ תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ])


def build_admin_sheets_keyboard() -> InlineKeyboardMarkup:
    """
    מקלדת לפעולות על הגיליונות
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 מידע על הגיליונות", callback_data="admin_sheets_info"),
        ],
        [
            InlineKeyboardButton("🔧 תיקון כותרות", callback_data="admin_sheets_fix"),
            InlineKeyboardButton("✔ בדיקת תקינות", callback_data="admin_sheets_validate"),
        ],
        [
            InlineKeyboardButton("🧹 ניקוי כפילויות", callback_data="admin_sheets_clear_dup"),
        ],
        [InlineKeyboardButton("↩️ חזרה לפאנל אדמין", callback_data=CALLBACK_MENU_ADMIN)],
    ])
