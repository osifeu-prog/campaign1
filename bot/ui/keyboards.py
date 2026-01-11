# bot/ui/keyboards.py
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional

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
    CALLBACK_ADMIN_SHEETS,
    CALLBACK_ADMIN_BROADCAST,
    CALLBACK_ADMIN_EXPORT,
    CALLBACK_ADMIN_QUICK_NAV,
    CALLBACK_EXPERT_PROFILE,
    CALLBACK_SUPPORT_EXPERT,
    CALLBACK_MY_PROFILE,
    CALLBACK_MY_STATS,
    CALLBACK_MY_REFERRALS,
    WHATSAPP_GROUP_LINK,
)


def build_start_keyboard() -> InlineKeyboardMarkup:
    """מקלדת לתחילת תהליך"""
    keyboard = [
        [InlineKeyboardButton("🧑‍🎓 הרשמה כתומך", callback_data=CALLBACK_APPLY_SUPPORTER)],
        [InlineKeyboardButton("🧠 הגשת מועמדות כמומחה", callback_data=CALLBACK_APPLY_EXPERT)],
        [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_start_carousel_keyboard(current_idx: int, total: int) -> InlineKeyboardMarkup:
    """מקלדת לניווט בקרוסלת התמונות"""
    buttons = []
    if current_idx > 0:
        buttons.append(InlineKeyboardButton("⬅️ הקודם", callback_data=f"start_slide:{current_idx-1}"))
    
    buttons.append(InlineKeyboardButton(f"{current_idx+1}/{total}", callback_data="noop"))
    
    if current_idx < total - 1:
        buttons.append(InlineKeyboardButton("הבא ➡️", callback_data=f"start_slide:{current_idx+1}"))
    
    rows = [buttons]
    
    # כפתור סיום אם זה האחרון
    if current_idx == total - 1:
        rows.append([InlineKeyboardButton("✅ הבנתי, המשך", callback_data="start_finish")])
    
    rows.append([InlineKeyboardButton("❓ מה זה סוציוקרטיה?", callback_data="start_soci")])
    
    return InlineKeyboardMarkup(rows)


def build_main_menu_for_user(user_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    """תפריט ראשי מותאם למשתמש"""
    from services.sheets_service import sheets_service
    
    supporter = sheets_service.get_supporter_by_id(str(user_id))
    expert = sheets_service.get_expert_by_id(str(user_id))
    
    rows = []
    
    # כפתורים בסיסיים
    if not supporter:
        rows.append([InlineKeyboardButton("🧑‍🎓 הרשמה כתומך", callback_data=CALLBACK_APPLY_SUPPORTER)])
    else:
        rows.append([InlineKeyboardButton("📊 פרופיל תומך", callback_data=CALLBACK_MENU_SUPPORT)])
        
        # כפתור וואטסאפ אם קיים והמשתמש רשום
        if WHATSAPP_GROUP_LINK:
            whatsapp_sent = sheets_service.get_whatsapp_sent_status(str(user_id))
            if not whatsapp_sent:
                rows.append([InlineKeyboardButton("📱 קבלת לינק וואטסאפ", callback_data="get_whatsapp")])
    
    if supporter and not expert:
        rows.append([InlineKeyboardButton("🧠 הגשת מועמדות כמומחה", callback_data=CALLBACK_APPLY_EXPERT)])
    elif expert:
        rows.append([InlineKeyboardButton("🧠 פאנל מומחה", callback_data=CALLBACK_MENU_EXPERT)])
    
    rows.append([InlineKeyboardButton("🏆 טבלת מובילים", callback_data=CALLBACK_LEADERBOARD)])
    rows.append([InlineKeyboardButton("📍 מקומות פנויים", callback_data=CALLBACK_MENU_POSITIONS)])
    rows.append([InlineKeyboardButton("💎 תמיכה בתרומה", callback_data=CALLBACK_DONATE)])
    rows.append([InlineKeyboardButton("❓ עזרה", callback_data=CALLBACK_HELP_INFO)])
    
    if is_admin:
        rows.append([InlineKeyboardButton("🛠️ פאנל אדמין", callback_data=CALLBACK_MENU_ADMIN)])
    
    return InlineKeyboardMarkup(rows)


def build_leaderboard_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """מקלדת לטבלת מובילים"""
    from services.sheets_service import sheets_service
    
    leaders = sheets_service.get_experts_leaderboard()
    rows = []
    
    # כפתורים למומחים המובילים (עד 5)
    for idx, expert in enumerate(leaders[:5], 1):
        name = expert.get("expert_full_name", f"מומחה {idx}")
        expert_id = expert.get("user_id", "")
        if expert_id:
            rows.append([InlineKeyboardButton(
                f"{idx}. {name}",
                callback_data=f"{CALLBACK_EXPERT_PROFILE}:{expert_id}"
            )])
    
    rows.append([InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)])
    
    if is_admin:
        rows.append([InlineKeyboardButton("🛠️ פאנל אדמין", callback_data=CALLBACK_MENU_ADMIN)])
    
    return InlineKeyboardMarkup(rows)


def build_expert_profile_keyboard(expert_id: str, is_viewer_admin: bool = False) -> InlineKeyboardMarkup:
    """מקלדת לפרופיל מומחה"""
    from services.sheets_service import sheets_service
    
    expert = sheets_service.get_expert_by_id(expert_id)
    rows = []
    
    if expert:
        # כפתור תמיכה במומחה
        rows.append([InlineKeyboardButton(
            "👍 תמוך במומחה זה", 
            callback_data=f"{CALLBACK_SUPPORT_EXPERT}:{expert_id}"
        )])
        
        # קישור שיתוף אם המומחה מאושר
        if expert.get("status") == "approved":
            from bot.handlers.expert_handlers import build_expert_referral_link
            # נצטרך את שם הבוט מהקונטקסט, אז נשתמש ב-callback במקום URL ישיר
            rows.append([InlineKeyboardButton(
                "📣 שתף מומחה זה", 
                callback_data=f"share_expert:{expert_id}"
            )])
    
    rows.append([InlineKeyboardButton("🏆 חזרה לטבלת מובילים", callback_data=CALLBACK_LEADERBOARD)])
    rows.append([InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)])
    
    if is_viewer_admin:
        rows.append([
            InlineKeyboardButton("✅ אישור", callback_data=f"expert_approve:{expert_id}"),
            InlineKeyboardButton("❌ דחייה", callback_data=f"expert_reject:{expert_id}")
        ])
    
    return InlineKeyboardMarkup(rows)


def build_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """מקלדת לפאנל אדמין"""
    rows = [
        [InlineKeyboardButton("📊 סטטיסטיקות", callback_data="admin_stats")],
        [InlineKeyboardButton("📋 ניהול גיליונות", callback_data=CALLBACK_ADMIN_SHEETS)],
        [InlineKeyboardButton("📢 שידור הודעות", callback_data=CALLBACK_ADMIN_BROADCAST)],
        [InlineKeyboardButton("📁 יצוא נתונים", callback_data=CALLBACK_ADMIN_EXPORT)],
        [InlineKeyboardButton("⚡ ניווט מהיר", callback_data=CALLBACK_ADMIN_QUICK_NAV)],
        [InlineKeyboardButton("👥 ניהול מומחים", callback_data="admin_experts")],
        [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ]
    return InlineKeyboardMarkup(rows)


def build_user_profile_keyboard(user_id: int, is_supporter: bool, is_expert: bool) -> InlineKeyboardMarkup:
    """מקלדת לפרופיל משתמש אישי"""
    rows = []
    
    if is_supporter:
        rows.append([InlineKeyboardButton("📊 סטטיסטיקות אישיות", callback_data=CALLBACK_MY_STATS)])
        rows.append([InlineKeyboardButton("👥 ההפניות שלי", callback_data=CALLBACK_MY_REFERRALS)])
    
    if is_expert:
        rows.append([InlineKeyboardButton("🧠 פרופיל מומחה", callback_data=CALLBACK_MENU_EXPERT)])
    
    rows.append([InlineKeyboardButton("🏆 טבלת מובילים", callback_data=CALLBACK_LEADERBOARD)])
    rows.append([InlineKeyboardButton("💎 תמיכה בתרומה", callback_data=CALLBACK_DONATE)])
    rows.append([InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)])
    
    return InlineKeyboardMarkup(rows)


def build_whatsapp_keyboard() -> InlineKeyboardMarkup:
    """מקלדת ללינק וואטסאפ"""
    if not WHATSAPP_GROUP_LINK:
        return build_main_menu_for_user(0, False)
    
    rows = [
        [InlineKeyboardButton("📱 הצטרפות לקבוצת וואטסאפ", url=WHATSAPP_GROUP_LINK)],
        [InlineKeyboardButton("✅ אישור קבלה", callback_data="whatsapp_confirmed")],
        [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
    ]
    return InlineKeyboardMarkup(rows)
