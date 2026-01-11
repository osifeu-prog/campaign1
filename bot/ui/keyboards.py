# bot/ui/keyboards.py
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional

from utils.constants import (
    CALLBACK_MENU_MAIN,
    CALLBACK_MENU_SUPPORT,
    CALLBACK_MENU_EXPERT,
    CALLBACK_MENU_ADMIN,
    CALLBACK_APPLY_SUPPORTER,
    CALLBACK_APPLY_EXPERT,
    CALLBACK_MENU_POSITIONS,
    CALLBACK_LEADERBOARD,
    CALLBACK_DONATE,
    CALLBACK_HELP_INFO,
)

# -----------------------
# Start keyboards (קרוסלה + סיום)
# -----------------------

def build_start_carousel_keyboard(slide_index: int, total_slides: int) -> InlineKeyboardMarkup:
    buttons = []
    nav_row = []
    if slide_index > 0:
        nav_row.append(InlineKeyboardButton("◀️ הקודם", callback_data=f"start_slide:{slide_index - 1}"))
    nav_row.append(InlineKeyboardButton(f"• {slide_index + 1}/{total_slides} •", callback_data="page_info"))
    if slide_index < total_slides - 1:
        nav_row.append(InlineKeyboardButton("הבא ▶️", callback_data=f"start_slide:{slide_index + 1}"))
    buttons.append(nav_row)

    # sociocracy + finish
    buttons.append([
        InlineKeyboardButton("📜 על סוציוקרטיה", callback_data="start_soci"),
        InlineKeyboardButton("✅ המשך", callback_data="start_finish"),
    ])

    return InlineKeyboardMarkup(buttons)

def build_start_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("🧑‍🎓 הצטרפות כתומך", callback_data=CALLBACK_APPLY_SUPPORTER),
            InlineKeyboardButton("🧠 הגשת מועמדות כמומחה", callback_data=CALLBACK_APPLY_EXPERT),
        ],
        [
            InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN),
            InlineKeyboardButton("ℹ️ עזרה ופקודות", callback_data=CALLBACK_HELP_INFO),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

# -----------------------
# Main menu
# -----------------------

def build_main_menu_for_user(user_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("🧑‍🎓 תומכים", callback_data=CALLBACK_MENU_SUPPORT),
            InlineKeyboardButton("🧠 מומחים", callback_data=CALLBACK_MENU_EXPERT),
        ],
        [
            InlineKeyboardButton("📍 מקומות", callback_data=CALLBACK_MENU_POSITIONS),
            InlineKeyboardButton("🏆 טבלת מובילים", callback_data=CALLBACK_LEADERBOARD),
        ],
        [
            InlineKeyboardButton("💎 לתרום", callback_data=CALLBACK_DONATE),
            InlineKeyboardButton("ℹ️ עזרה ופקודות", callback_data=CALLBACK_HELP_INFO),
        ],
    ]

    if is_admin:
        buttons.append([InlineKeyboardButton("🛠️ פאנל אדמין", callback_data=CALLBACK_MENU_ADMIN)])

    return InlineKeyboardMarkup(buttons)

# -----------------------
# Admin keyboards (קיימים)
# -----------------------

def build_admin_panel_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("📊 ניהול גיליונות", callback_data="admin_sheets"),
            InlineKeyboardButton("📣 שידור", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton("📁 יצוא נתונים", callback_data="admin_export"),
            InlineKeyboardButton("🧭 ניווט מהיר", callback_data="admin_quick_nav"),
        ],
        [
            InlineKeyboardButton("🔙 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

def build_admin_sheets_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("ℹ️ מידע על הגיליונות", callback_data="admin_sheets_info")],
        [InlineKeyboardButton("🔧 תיקון כותרות", callback_data="admin_sheets_fix"),
         InlineKeyboardButton("✔ בדיקת תקינות", callback_data="admin_sheets_validate")],
        [InlineKeyboardButton("🧹 ניקוי כפילויות", callback_data="admin_sheets_clear_dup")],
        [InlineKeyboardButton("🔙 חזרה לפאנל אדמין", callback_data=CALLBACK_MENU_ADMIN)],
    ]
    return InlineKeyboardMarkup(buttons)

# -----------------------
# Leaderboard keyboards
# -----------------------

def build_leaderboard_keyboard(show_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if show_admin:
        buttons.append([InlineKeyboardButton("🔄 רענון נתונים", callback_data="leaderboard_refresh")])
    buttons.append([InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)])
    return InlineKeyboardMarkup(buttons)

def build_expert_profile_keyboard(expert_user_id: str, is_viewer_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("👍 תמיכה במומחה זה", callback_data=f"support_expert:{expert_user_id}")],
        [InlineKeyboardButton("🔙 חזרה ל-Leaderboard", callback_data=CALLBACK_LEADERBOARD)],
    ]
    if is_viewer_admin:
        buttons.insert(0, [InlineKeyboardButton("✏️ עריכה", callback_data=f"admin_edit_expert:{expert_user_id}"),
                           InlineKeyboardButton("📊 סטטיסטיקות", callback_data=f"admin_expert_stats:{expert_user_id}")])
    return InlineKeyboardMarkup(buttons)

# -----------------------
# Donation keyboard (מופיע גם ב־donation_handlers)
# -----------------------

def build_donation_keyboard() -> InlineKeyboardMarkup:
    from utils.constants import TON_WALLET_ADDRESS, MIN_DONATION_AMOUNT
    ton_link = f"ton://transfer/{TON_WALLET_ADDRESS}"
    buttons = [
        [InlineKeyboardButton(f"💎 לתרום {MIN_DONATION_AMOUNT} TON", url=f"{ton_link}?amount={int(MIN_DONATION_AMOUNT * 1e9)}")],
        [InlineKeyboardButton("💎 לתרום 5 TON", url=f"{ton_link}?amount={int(5 * 1e9)}")],
        [InlineKeyboardButton("💎 לתרום 10 TON", url=f"{ton_link}?amount={int(10 * 1e9)}")],
        [InlineKeyboardButton("💎 לתרום סכום מותאם אישית", url=ton_link)],
        [InlineKeyboardButton("📋 העתקת כתובת ארנק", callback_data="copy_wallet")],
        [InlineKeyboardButton("ℹ️ מה זה TON?", callback_data="ton_info")],
        [InlineKeyboardButton("🔙 חזרה לתפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ]
    return InlineKeyboardMarkup(buttons)
