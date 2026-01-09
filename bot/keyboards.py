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
)


def build_main_menu_for_user(user_id: int, is_admin: bool) -> InlineKeyboardMarkup:
    """
    בניית תפריט ראשי לפי האם המשתמש אדמין
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
        [InlineKeyboardButton("📣 לשתף את הקישור שלי", url=personal_link)],
        [InlineKeyboardButton("🧠 להגיש מועמדות כמומחה", callback_data=CALLBACK_MENU_EXPERT)],
        [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ])


def build_expert_panel_keyboard(status: str, referral_link: str | None) -> InlineKeyboardMarkup:
    """
    מקלדת למסך 'פאנל מומחה'
    """
    buttons = []

    if status == "approved" and referral_link:
        buttons.append([InlineKeyboardButton("📣 לשתף את הקישור שלי", url=referral_link)])

    if status in ("rejected", "approved"):
        buttons.append([InlineKeyboardButton("🧠 הגשת מועמדות מחדש", callback_data=CALLBACK_APPLY_EXPERT)])

    buttons.append([InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)])

    return InlineKeyboardMarkup(buttons)


def build_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """
    מקלדת לפאנל אדמין
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 מומחים ממתינים", callback_data=CALLBACK_ADMIN_PENDING_EXPERTS)],
        [InlineKeyboardButton("📊 רשימת מקומות", callback_data=CALLBACK_MENU_POSITIONS)],
        [InlineKeyboardButton("🧩 ניהול קבוצות", callback_data=CALLBACK_ADMIN_GROUPS)],
        [InlineKeyboardButton("↩️ תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ])
