# bot/ui/keyboards.py
# ==========================================
# כל המקלדות של הבוט: תפריט ראשי, מומחה, תומך, אדמין, קרוסלה
# ==========================================

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from utils.constants import (
    CALLBACK_MENU_MAIN,
    CALLBACK_MENU_SUPPORT,
    CALLBACK_MENU_EXPERT,
    CALLBACK_MENU_ADMIN,
    CALLBACK_MENU_POSITIONS,
    CALLBACK_APPLY_SUPPORTER,
    CALLBACK_APPLY_EXPERT,
    CALLBACK_LEADERBOARD,
    CALLBACK_DONATE,
    CALLBACK_HELP_INFO,
    CALLBACK_START_SLIDE,
    CALLBACK_START_SOCI,
    CALLBACK_START_FINISH,
    CALLBACK_EXPERT_PROFILE,
)


# ===============================
# Start carousel
# ===============================

def build_start_carousel_keyboard(index: int, total: int):
    buttons = []

    # Previous
    if index > 0:
        buttons.append(
            InlineKeyboardButton("⬅️", callback_data=f"{CALLBACK_START_SLIDE}:{index - 1}")
        )
    else:
        buttons.append(InlineKeyboardButton(" ", callback_data="noop"))

    # Next
    if index < total - 1:
        buttons.append(
            InlineKeyboardButton("➡️", callback_data=f"{CALLBACK_START_SLIDE}:{index + 1}")
        )
    else:
        buttons.append(InlineKeyboardButton(" ", callback_data="noop"))

    bottom = [
        InlineKeyboardButton("ℹ️ סוציוקרטיה", callback_data=CALLBACK_START_SOCI),
        InlineKeyboardButton("🚀 המשך", callback_data=CALLBACK_START_FINISH),
    ]

    return InlineKeyboardMarkup([buttons, bottom])


# ===============================
# Start keyboard (after carousel)
# ===============================

def build_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ])


# ===============================
# Main menu
# ===============================
# בתוך build_main_menu_for_user ב-bot/ui/keyboards.py

def build_main_menu_for_user(user_id: int, is_admin: bool):
    rows = [
        [InlineKeyboardButton("🧑‍🎓 תומך", callback_data=CALLBACK_MENU_SUPPORT)],
        [InlineKeyboardButton("🧠 מומחה", callback_data=CALLBACK_MENU_EXPERT)],
        [InlineKeyboardButton("🏆 טבלת מובילים", callback_data=CALLBACK_LEADERBOARD)],
        [InlineKeyboardButton("📍 רשימת מקומות", callback_data=CALLBACK_MENU_POSITIONS)],
        [InlineKeyboardButton("💎 תרומה", callback_data=CALLBACK_DONATE)],
        [InlineKeyboardButton("ℹ️ עזרה", callback_data=CALLBACK_HELP_INFO)],
        
    ]

    if is_admin:
        rows.append([InlineKeyboardButton("🛠️ אדמין", callback_data=CALLBACK_MENU_ADMIN)])

    return InlineKeyboardMarkup(rows)

# ===============================
# Leaderboard keyboard
# ===============================

def build_leaderboard_keyboard(is_admin: bool):
    rows = [
        [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ]
    return InlineKeyboardMarkup(rows)


# ===============================
# Expert profile keyboard
# ===============================

def build_expert_profile_keyboard(expert_id: str, is_viewer_admin: bool):
    rows = [
        [InlineKeyboardButton("🙌 תמיכה במומחה זה", callback_data=f"support_expert:{expert_id}")],
        [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ]

    if is_viewer_admin:
        rows.insert(0, [
            InlineKeyboardButton("✔ לאשר", callback_data=f"expert_approve:{expert_id}"),
            InlineKeyboardButton("❌ לדחות", callback_data=f"expert_reject:{expert_id}"),
        ])

    return InlineKeyboardMarkup(rows)


# ===============================
# Admin panel keyboard
# ===============================

def build_admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📍 מקומות", callback_data=CALLBACK_MENU_POSITIONS),
            InlineKeyboardButton("🏆 מובילים", callback_data=CALLBACK_LEADERBOARD),
        ],
        [
            InlineKeyboardButton("🧑‍🎓 תומכים", callback_data="admin_supporters"),
            InlineKeyboardButton("🧠 מומחים", callback_data="admin_experts"),
        ],
        [
            InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN),
        ]
    ])
