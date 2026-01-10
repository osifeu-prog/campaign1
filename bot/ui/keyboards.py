# ===============================
# bot/ui/keyboards.py - UI משודרג
# ===============================

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utils.constants import *


# ===============================
# תפריט ראשי לפי סוג משתמש
# ===============================

def build_main_menu_for_user(user_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    תפריט ראשי דינמי לפי הרשאות
    """
    buttons = []
    
    # שורה 1: תפריטים אישיים
    buttons.append([
        InlineKeyboardButton("👤 פרופיל תומך", callback_data=CALLBACK_MENU_SUPPORT),
        InlineKeyboardButton("🧠 פרופיל מומחה", callback_data=CALLBACK_MENU_EXPERT),
    ])
    
    # שורה 2: מידע ופעולות
    buttons.append([
        InlineKeyboardButton("🎯 רשימת המקומות", callback_data=CALLBACK_MENU_POSITIONS),
        InlineKeyboardButton("🏆 טבלת מובילים", callback_data=CALLBACK_LEADERBOARD),
    ])
    
    # שורה 3: תרומה
    buttons.append([
        InlineKeyboardButton("💎 לתמוך בפרויקט (TON)", callback_data=CALLBACK_DONATE),
    ])
    
    # שורה 4: אדמין (אם רלוונטי)
    if is_admin:
        buttons.append([
            InlineKeyboardButton("🛠️ פאנל אדמין", callback_data=CALLBACK_MENU_ADMIN),
        ])
    
    # שורה 5: מידע
    buttons.append([
        InlineKeyboardButton("ℹ️ עזרה ופקודות", callback_data="help_info"),
    ])
    
    return InlineKeyboardMarkup(buttons)


# ===============================
# תפריט Start - קרוסלה
# ===============================

def build_start_carousel_keyboard(slide_index: int, total_slides: int) -> InlineKeyboardMarkup:
    """
    מקלדת קרוסלה משופרת עם אינדיקטור התקדמות
    """
    buttons = []
    
    # שורת ניווט
    nav_row = []
    if slide_index > 0:
        nav_row.append(InlineKeyboardButton(
            "◀️ הקודם",
            callback_data=f"{CALLBACK_START_SLIDE}:{slide_index - 1}"
        ))
    
    # אינדיקטור מיקום
    nav_row.append(InlineKeyboardButton(
        f"• {slide_index + 1}/{total_slides} •",
        callback_data="slide_info"
    ))
    
    if slide_index < total_slides - 1:
        nav_row.append(InlineKeyboardButton(
            "הבא ▶️",
            callback_data=f"{CALLBACK_START_SLIDE}:{slide_index + 1}"
        ))
    
    buttons.append(nav_row)
    
    # כפתורים נוספים
    if slide_index == total_slides - 1:
        # בסלייד האחרון - כפתור סיום
        buttons.append([
            InlineKeyboardButton(
                "✅ בואו נתחיל!",
                callback_data=CALLBACK_START_FINISH
            )
        ])
    
    # כפתור סוציוקרטיה בכל סלייד
    buttons.append([
        InlineKeyboardButton(
            "📖 מה זה סוציוקרטיה?",
            callback_data=CALLBACK_START_SOCI
        )
    ])
    
    # דילוג לסוף
    if slide_index < total_slides - 2:
        buttons.append([
            InlineKeyboardButton(
                "⏭️ דילוג להתחלה",
                callback_data=CALLBACK_START_FINISH
            )
        ])
    
    return InlineKeyboardMarkup(buttons)


def build_start_keyboard() -> InlineKeyboardMarkup:
    """
    מקלדת Start לאחר הקרוסלה
    """
    buttons = [
        [
            InlineKeyboardButton(
                "🧑‍🎓 הרשמה כתומך",
                callback_data=CALLBACK_APPLY_SUPPORTER
            ),
        ],
        [
            InlineKeyboardButton(
                "🧠 הגשת מועמדות כמומחה",
                callback_data=CALLBACK_APPLY_EXPERT
            ),
        ],
        [
            InlineKeyboardButton(
                "🏆 צפייה בטבלת מובילים",
                callback_data=CALLBACK_LEADERBOARD
            ),
        ],
        [
            InlineKeyboardButton(
                "💎 תמיכה בפרויקט",
                callback_data=CALLBACK_DONATE
            ),
        ],
        [
            InlineKeyboardButton(
                "📋 תפריט ראשי",
                callback_data=CALLBACK_MENU_MAIN
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(buttons)


# ===============================
# תפריט אדמין
# ===============================

def build_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """
    פאנל אדמין משודרג
    """
    buttons = [
        # שורה 1: ניהול
        [
            InlineKeyboardButton(
                "📊 Dashboard",
                callback_data="admin_dashboard"
            ),
            InlineKeyboardButton(
                "📈 סטטיסטיקות",
                callback_data="admin_stats"
            ),
        ],
        # שורה 2: גיליונות
        [
            InlineKeyboardButton(
                "📋 ניהול גיליונות",
                callback_data=CALLBACK_ADMIN_SHEETS
            ),
        ],
        # שורה 3: מומחים
        [
            InlineKeyboardButton(
                "🧠 מומחים ממתינים",
                callback_data="admin_pending_experts"
            ),
            InlineKeyboardButton(
                "🏆 Leaderboard",
                callback_data=CALLBACK_LEADERBOARD
            ),
        ],
        # שורה 4: שידור
        [
            InlineKeyboardButton(
                "📣 שידור הודעות",
                callback_data=CALLBACK_ADMIN_BROADCAST
            ),
        ],
        # שורה 5: ייצוא
        [
            InlineKeyboardButton(
                "📁 ייצוא נתונים",
                callback_data=CALLBACK_ADMIN_EXPORT
            ),
            InlineKeyboardButton(
                "🧭 ניווט מהיר",
                callback_data=CALLBACK_ADMIN_QUICK_NAV
            ),
        ],
        # שורה 6: חזרה
        [
            InlineKeyboardButton(
                "🔙 תפריט ראשי",
                callback_data=CALLBACK_MENU_MAIN
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(buttons)


def build_admin_sheets_keyboard() -> InlineKeyboardMarkup:
    """
    תפריט ניהול גיליונות
    """
    buttons = [
        [
            InlineKeyboardButton(
                "ℹ️ מידע על הגיליונות",
                callback_data=CALLBACK_ADMIN_SHEETS_INFO
            ),
        ],
        [
            InlineKeyboardButton(
                "🔧 תיקון כותרות",
                callback_data=CALLBACK_ADMIN_SHEETS_FIX
            ),
            InlineKeyboardButton(
                "✔ בדיקת תקינות",
                callback_data=CALLBACK_ADMIN_SHEETS_VALIDATE
            ),
        ],
        [
            InlineKeyboardButton(
                "🧹 ניקוי כפילויות",
                callback_data=CALLBACK_ADMIN_SHEETS_CLEAR_DUP
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 חזרה לפאנל אדמין",
                callback_data=CALLBACK_MENU_ADMIN
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(buttons)


# ===============================
# Leaderboard
# ===============================

def build_leaderboard_keyboard(show_admin: bool = False) -> InlineKeyboardMarkup:
    """
    מקלדת לטבלת מובילים
    """
    buttons = []
    
    if show_admin:
        buttons.append([
            InlineKeyboardButton(
                "🔄 רענון נתונים",
                callback_data="leaderboard_refresh"
            ),
        ])
    
    buttons.extend([
        [
            InlineKeyboardButton(
                "📋 תפריט ראשי",
                callback_data=CALLBACK_MENU_MAIN
            ),
        ],
    ])
    
    return InlineKeyboardMarkup(buttons)


def build_expert_profile_keyboard(expert_user_id: str, is_viewer_admin: bool = False) -> InlineKeyboardMarkup:
    """
    מקלדת לפרופיל מומחה ציבורי
    """
    buttons = []
    
    # כפתור תמיכה במומחה
    buttons.append([
        InlineKeyboardButton(
            f"👍 תמיכה במומחה זה",
            callback_data=f"support_expert:{expert_user_id}"
        ),
    ])
    
    # כפתורי אדמין
    if is_viewer_admin:
        buttons.append([
            InlineKeyboardButton(
                "✏️ עריכה",
                callback_data=f"admin_edit_expert:{expert_user_id}"
            ),
            InlineKeyboardButton(
                "📊 סטטיסטיקות",
                callback_data=f"admin_expert_stats:{expert_user_id}"
            ),
        ])
    
    # חזרה
    buttons.append([
        InlineKeyboardButton(
            "🔙 חזרה ל-Leaderboard",
            callback_data=CALLBACK_LEADERBOARD
        ),
    ])
    
    return InlineKeyboardMarkup(buttons)


# ===============================
# Pagination
# ===============================

def build_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str,
    include_back: bool = True,
    back_callback: str = "menu_main"
) -> InlineKeyboardMarkup:
    """
    מקלדת pagination גנרית ומשופרת
    """
    buttons = []
    nav_row = []
    
    # ניווט
    if current_page > 0:
        nav_row.append(InlineKeyboardButton(
            "◀️ הקודם",
            callback_data=f"{callback_prefix}:{current_page - 1}"
        ))
    
    # מיקום נוכחי
    nav_row.append(InlineKeyboardButton(
        f"• {current_page + 1}/{total_pages} •",
        callback_data="page_info"
    ))
    
    if current_page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            "הבא ▶️",
            callback_data=f"{callback_prefix}:{current_page + 1}"
        ))
    
    buttons.append(nav_row)
    
    # קפיצה מהירה (אם יש יותר מ-5 עמודים)
    if total_pages > 5:
        jump_row = []
        
        # דף ראשון
        if current_page > 2:
            jump_row.append(InlineKeyboardButton(
                "⏮️ ראשון",
                callback_data=f"{callback_prefix}:0"
            ))
        
        # דף אחרון
        if current_page < total_pages - 3:
            jump_row.append(InlineKeyboardButton(
                "אחרון ⏭️",
                callback_data=f"{callback_prefix}:{total_pages - 1}"
            ))
        
        if jump_row:
            buttons.append(jump_row)
    
    # חזרה
    if include_back:
        buttons.append([
            InlineKeyboardButton(
                "🔙 חזרה",
                callback_data=back_callback
            ),
        ])
    
    return InlineKeyboardMarkup(buttons)
