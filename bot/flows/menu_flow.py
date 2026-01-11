# bot/flows/menu_flow.py
# ===============================
# תפריט ראשי, תומך, מומחה, אדמין, Leaderboard, Positions
# ===============================

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from bot.core.session_manager import session_manager
from bot.core.telemetry import telemetry
from bot.ui.keyboards import (
    build_main_menu_for_user,
    build_leaderboard_keyboard,
    build_expert_profile_keyboard,
)
from bot.states import SUPPORTER_NAME, EXPERT_NAME
from services import sheets_service
from services.logger_service import log
from utils.constants import (
    ADMIN_IDS,
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
    WHATSAPP_GROUP_LINK,
)


def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS


# ===============================
# /menu command
# ===============================

async def handle_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log(context, "Menu command", user=user)
    # Update last activity
    sheets_service.update_user_last_activity(str(user.id))
    keyboard = build_main_menu_for_user(user.id, is_admin(user.id))
    await update.message.reply_text("📋 תפריט ראשי", reply_markup=keyboard)


# ===============================
# Callback router
# ===============================

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers import admin_handlers

    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    bot_username = context.bot.username

    session_manager.get_or_create(user)
    
    # Update last activity
    sheets_service.update_user_last_activity(str(user.id))

    # תפריט ראשי
    if data == CALLBACK_MENU_MAIN:
        await log(context, "Open main menu (callback)", user=user)
        keyboard = build_main_menu_for_user(user.id, is_admin(user.id))
        await query.message.reply_text("📋 תפריט ראשי", reply_markup=keyboard)
        await telemetry.track_event(context, "menu_main_open", user=user)
        return ConversationHandler.END

    # תומך
    if data == CALLBACK_MENU_SUPPORT:
        await log(context, "Open supporter menu", user=user)
        supporter = sheets_service.get_supporter_by_id(str(user.id))
        personal_link = f"https://t.me/{bot_username}?start={user.id}"

        if supporter:
            text = (
                "פרופיל תומך:\n\n"
                f"שם: {supporter.get('full_name_telegram', user.full_name)}\n"
                f"עיר: {supporter.get('city', 'לא צויין')}\n"
                f"אימייל: {supporter.get('email', 'לא צויין')}\n\n"
                "הקישור האישי שלך לשיתוף:\n"
                f"{personal_link}\n\n"
            )
            
            # הוסף לינק וואטסאפ אם קיים
            if WHATSAPP_GROUP_LINK:
                whatsapp_sent = sheets_service.get_whatsapp_sent_status(str(user.id))
                if whatsapp_sent:
                    text += f"📱 קבוצת וואטסאפ: {WHATSAPP_GROUP_LINK}\n\n"
                else:
                    text += "📱 לחץ /whatsapp לקבלת לינק לקבוצת וואטסאפ\n\n"
            
            text += "מה תרצה לעשות עכשיו?"
            
            keyboard_buttons = [
                [InlineKeyboardButton("📣 לשתף את הקישור האישי", url=personal_link)],
                [InlineKeyboardButton("🧠 להגיש מועמדות כמומחה", callback_data=CALLBACK_APPLY_EXPERT)],
            ]
            
            if WHATSAPP_GROUP_LINK and not whatsapp_sent:
                keyboard_buttons.insert(1, [InlineKeyboardButton("📱 קבלת לינק וואטסאפ", callback_data="get_whatsapp")])
            
            keyboard_buttons.append([InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
        else:
            text = (
                "עדיין לא נרשמת כתומך.\n\n"
                "כדי להירשם כתומך:\n"
                "לחץ על הכפתור למטה ונרוץ יחד על התהליך."
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🧑‍🎓 התחלת הרשמת תומך", callback_data=CALLBACK_APPLY_SUPPORTER)],
                [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
            ])

        await query.message.reply_text(text, reply_markup=keyboard)
        await telemetry.track_event(context, "menu_support_open", user=user)
        return ConversationHandler.END

    # מומחה
    if data == CALLBACK_MENU_EXPERT:
        await log(context, "Open expert menu", user=user)
        
        # בדיקה אם המשתמש רשום כתומך לפני הרשמה כמומחה
        supporter = sheets_service.get_supporter_by_id(str(user.id))
        if not supporter:
            text = (
                "❌ לפני הגשת מועמדות כמומחה, עליך להירשם קודם כתומך.\n\n"
                "הרשמה כתומך מאפשרת לך:\n"
                "• להיות חלק מהקהילה\n"
                "• לקבל עדכונים שוטפים\n"
                "• לקבל לינק לקבוצת הוואטסאפ\n"
                "• לצבור נקודות ולהתקדם ברמות\n\n"
                "לחץ על הכפתור למטה כדי להירשם כתומך:"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🧑‍🎓 הירשם כתומך קודם", callback_data=CALLBACK_APPLY_SUPPORTER)],
                [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
            ])
            await query.message.reply_text(text, reply_markup=keyboard)
            await telemetry.track_event(context, "menu_expert_open_not_registered", user=user)
            return ConversationHandler.END
        
        status = sheets_service.get_expert_status(str(user.id))
        position = sheets_service.get_expert_position(str(user.id))
        group_link = sheets_service.get_expert_group_link(str(user.id))
        from bot.handlers.expert_handlers import build_expert_referral_link
        referral_link = build_expert_referral_link(bot_username, user.id)

        if status is None:
            text = (
                "אתה רשום כתומך ✅\n\n"
                "כעת אתה יכול להגיש מועמדות כמומחה.\n\n"
                "מה זה אומר?\n"
                "• תוכל לקבל מקום קבוע בתנועה\n"
                "• תוכל לצבור תומכים אישיים\n"
                "• תופיע בטבלת המובילים\n"
                "• תקבל גישה לחומרי העשרה\n\n"
                "לחץ על הכפתור למטה כדי להתחיל בתהליך:"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🧠 הגשת מועמדות כמומחה", callback_data=CALLBACK_APPLY_EXPERT)],
                [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
            ])
            await query.message.reply_text(text, reply_markup=keyboard)
            await telemetry.track_event(context, "menu_expert_open_no_application", user=user)
            return ConversationHandler.END

        status_text_map = {
            "pending": "⏳ ממתין לאישור",
            "approved": "✅ מאושר",
            "rejected": "❌ נדחה",
        }
        status_text = status_text_map.get(status, status or "לא ידוע")
        pos_text = position or "לא נבחר"

        text = (
            "פאנל מומחה:\n\n"
            f"סטטוס המועמדות שלך: {status_text}\n"
            f"מקום שבחרת: {pos_text}\n\n"
        )

        if status == "approved":
            text += (
                "המועמדות שלך אושרה! 🎉\n\n"
                "קישור הבוט האישי שלך לשיתוף (מומחה):\n"
                f"{referral_link}\n\n"
            )
            if group_link:
                text += f"קישור לקבוצה שלך:\n{group_link}\n\n"
            else:
                text += (
                    "עדיין לא הוגדר קישור לקבוצה שלך.\n"
                    "האדמין יכול להגדיר זאת עם:\n"
                    "/set_expert_group <user_id> <link>\n\n"
                )
        elif status == "pending":
            text += "המועמדות שלך ממתינה לאישור אדמין.\nתקבל הודעה כשתאושר.\n\n"
        elif status == "rejected":
            text += (
                "המועמדות שלך נדחתה.\n"
                "תוכל להגיש מועמדות מחדש בכל עת.\n\n"
            )

        text += "מה תרצה לעשות עכשיו?"

        keyboard_buttons = []
        if status == "approved":
            keyboard_buttons.append([InlineKeyboardButton("📣 לשתף את קישור המומחה", url=referral_link)])
        
        keyboard_buttons.append([InlineKeyboardButton("🧠 הגשת מועמדות מחדש", callback_data=CALLBACK_APPLY_EXPERT)])
        keyboard_buttons.append([InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)])

        keyboard = InlineKeyboardMarkup(keyboard_buttons)

        await query.message.reply_text(text, reply_markup=keyboard)
        await telemetry.track_event(context, "menu_expert_open", user=user, properties={"status": status})
        return ConversationHandler.END

    # קבלת לינק וואטסאפ
    if data == "get_whatsapp":
        if not WHATSAPP_GROUP_LINK:
            await query.message.reply_text("לינק קבוצת וואטסאפ לא זמין כרגע.")
            return ConversationHandler.END
        
        await query.message.reply_text(
            f"קבוצת הוואטסאפ של תנועת אחדות:\n\n{WHATSAPP_GROUP_LINK}\n\n"
            "הצטרפו כדי להיות חלק מהקהילה ולהישאר מעודכנים!"
        )
        
        # סמן שנשלח הלינק
        sheets_service.mark_whatsapp_sent(str(user.id))
        
        # נקודות על קבלת לינק וואטסאפ
        from services.level_service import level_service
        try:
            level_service.add_points(user.id, "supporter", 5)
        except Exception:
            pass
        
        return ConversationHandler.END

    # אדמין
    if data == CALLBACK_MENU_ADMIN:
        if not is_admin(user.id):
            await query.message.reply_text("אין לך הרשאה לצפות בפאנל האדמין.")
            return ConversationHandler.END

        await log(context, "Open admin panel", user=user)
        text = (
            "🛠️ פאנל אדמין:\n\n"
            "באפשרותך להשתמש בפקודות או בכפתורים שלמטה.\n"
        )
        from bot.ui.keyboards import build_admin_panel_keyboard
        await query.message.reply_text(text, reply_markup=build_admin_panel_keyboard())
        await telemetry.track_event(context, "menu_admin_open", user=user)
        return ConversationHandler.END

    # הרשמת תומך
    if data == CALLBACK_APPLY_SUPPORTER:
        await log(context, "User chose apply supporter from menu", user=user)
        await telemetry.track_event(context, "apply_supporter_clicked", user=user)
        await query.message.reply_text("מתחילים בהרשמת תומך. איך קוראים לך?")
        return SUPPORTER_NAME

    # הרשמת מומחה
    if data == CALLBACK_APPLY_EXPERT:
        await log(context, "User chose apply expert from menu", user=user)
        
        # בדיקה אם רשום כתומך
        supporter = sheets_service.get_supporter_by_id(str(user.id))
        if not supporter:
            await query.message.reply_text(
                "❌ לפני הגשת מועמדות כמומחה, עליך להירשם קודם כתומך.\n\n"
                "השתמש בתפריט ובחר 'תומך' כדי להירשם קודם."
            )
            return ConversationHandler.END
        
        await telemetry.track_event(context, "apply_expert_clicked", user=user)
        await query.message.reply_text("מתחילים בהגשת מועמדות כמומחה. מה שמך המלא?")
        return EXPERT_NAME

    # מקומות
    if data == CALLBACK_MENU_POSITIONS:
        positions = sheets_service.get_positions()
        await log(context, "View positions from menu", user=user, extra={"positions_count": len(positions)})
        text = "רשימת המקומות:\n\n"
        for pos in positions:
            status = "תפוס" if pos.get("expert_user_id") else "פנוי"
            text += f"{pos.get('position_id')}. {pos.get('title')} - {status}\n"
        await query.message.reply_text(text, reply_markup=build_main_menu_for_user(user.id, is_admin(user.id)))
        await telemetry.track_event(context, "positions_view", user=user, properties={"count": len(positions)})
        return ConversationHandler.END

    # Leaderboard
    if data == CALLBACK_LEADERBOARD:
        await log(context, "Open leaderboard", user=user)
        leaders = sheets_service.get_experts_leaderboard()
        if not leaders:
            await query.message.reply_text("אין מומחים בדירוג כרגע.", reply_markup=build_leaderboard_keyboard(is_admin(user.id)))
            return ConversationHandler.END

        text = "🏆 טבלת מובילים - מומחים לפי מספר תומכים:\n\n"
        for idx, row in enumerate(leaders, start=1):
            name = row.get("expert_full_name", "—")
            pos = row.get("expert_position", "—")
            supporters = row.get("supporters_count", 0)
            text += f"{idx}. {name} — מקום {pos} — תומכים: {supporters}\n"

        text += "\nבחר מומחה לצפייה בפרופיל."
        await query.message.reply_text(text, reply_markup=build_leaderboard_keyboard(is_admin(user.id)))
        await telemetry.track_event(context, "leaderboard_open", user=user)
        return ConversationHandler.END

    # פרופיל מומחה ציבורי
    if data and data.startswith("expert_profile:"):
        _, expert_id = data.split(":", 1)
        expert = sheets_service.get_expert_by_id(expert_id)
        if not expert:
            await query.message.reply_text("מומחה לא נמצא.")
            return ConversationHandler.END

        text = (
            f"🧠 פרופיל מומחה:\n\n"
            f"שם: {expert.get('expert_full_name', '')}\n"
            f"תחום: {expert.get('expert_field', '')}\n"
            f"ניסיון: {expert.get('expert_experience', '')}\n"
            f"מקום: {expert.get('expert_position', '')}\n"
            f"סטטוס: {expert.get('status', '')}\n"
            f"תומכים: {expert.get('supporters_count', 0)}\n"
            f"קישורים: {expert.get('expert_links', '')}\n"
        )
        keyboard = build_expert_profile_keyboard(expert_id, is_viewer_admin=is_admin(user.id))
        await query.message.reply_text(text, reply_markup=keyboard)
        return ConversationHandler.END

    # תמיכה במומחה
    if data and data.startswith("support_expert:"):
        from bot.handlers.expert_handlers import handle_support_expert_callback
        await handle_support_expert_callback(update, context)
        return ConversationHandler.END

    # תרומות
    if data == CALLBACK_DONATE:
        from bot.handlers.donation_handlers import handle_donation_callback
        await handle_donation_callback(update, context)
        return ConversationHandler.END

    # עזרה
    if data == CALLBACK_HELP_INFO:
        text = (
            "ℹ️ עזרה ופקודות:\n\n"
            "/start – התחלה\n"
            "/menu – תפריט ראשי\n"
            "/leaderboard – טבלת מובילים\n"
            "/myid – הצגת ה־user_id שלך\n"
            "/groupid – הצגת group id (בקבוצה)\n"
        )
        await query.message.reply_text(text)
        return ConversationHandler.END

    # ברירת מחדל לאדמין
    await admin_handlers.handle_admin_callback(query, context)
    return ConversationHandler.END
