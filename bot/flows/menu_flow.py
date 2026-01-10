# ===============================
# menu_flow – תפריטים, callbacks, smart fallback בסיסי
# ===============================

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from bot.core.session_manager import session_manager
from bot.core.telemetry import telemetry
from bot.ui.keyboards import build_main_menu_for_user
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
)


def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS


async def handle_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log(context, "Menu command", user=user)
    keyboard = build_main_menu_for_user(user.id, is_admin(user.id))
    await update.message.reply_text("📋 תפריט ראשי", reply_markup=keyboard)


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers import admin_handlers

    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    bot_username = context.bot.username
    session_manager.get_or_create(user)

    if data == CALLBACK_MENU_MAIN:
        await log(context, "Open main menu (callback)", user=user)
        keyboard = build_main_menu_for_user(user.id, is_admin(user.id))
        await query.message.reply_text("📋 תפריט ראשי", reply_markup=keyboard)
        await telemetry.track_event(context, "menu_main_open", user=user)
        return ConversationHandler.END

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
                "מה תרצה לעשות עכשיו?"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📣 לשתף את הקישור האישי", url=personal_link)],
                [InlineKeyboardButton("🧠 להגיש מועמדות כמומחה", callback_data=CALLBACK_MENU_EXPERT)],
                [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
            ])
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

    if data == CALLBACK_MENU_EXPERT:
        await log(context, "Open expert menu", user=user)

        status = sheets_service.get_expert_status(str(user.id))
        position = sheets_service.get_expert_position(str(user.id))
        group_link = sheets_service.get_expert_group_link(str(user.id))

        from bot.handlers.expert_handlers import build_expert_referral_link
        referral_link = build_expert_referral_link(bot_username, user.id)

        if status is None:
            text = (
                "עדיין לא הגשת מועמדות כמומחה.\n\n"
                "כדי להגיש מועמדות:\n"
                "לחץ על הכפתור למטה ונרוץ יחד על התהליך."
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🧠 הגשת מועמדות כמומחה", callback_data=CALLBACK_APPLY_EXPERT)],
                [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
            ])
            await query.message.reply_text(text, reply_markup=keyboard)
            await telemetry.track_event(context, "menu_expert_open_no_application", user=user)
            return ConversationHandler.END

        status_text_map = {
            "pending": "ממתין לאישור",
            "approved": "מאושר",
            "rejected": "נדחה",
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
                "המועמדות שלך אושרה.\n\n"
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
            text += "המועמדות שלך ממתינה לאישור אדמין.\n\n"
        elif status == "rejected":
            text += (
                "המועמדות שלך נדחתה.\n"
                "תוכל להגיש מועמדות מחדש בכל עת.\n\n"
            )

        text += "מה תרצה לעשות עכשיו?"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📣 לשתף את קישור המומחה", url=referral_link)],
            [InlineKeyboardButton("🧠 הגשת מועמדות מחדש", callback_data=CALLBACK_APPLY_EXPERT)],
            [InlineKeyboardButton("📋 תפריט ראשי", callback_data=CALLBACK_MENU_MAIN)],
        ])

        await query.message.reply_text(text, reply_markup=keyboard)
        await telemetry.track_event(context, "menu_expert_open", user=user, properties={"status": status})
        return ConversationHandler.END

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

    if data == CALLBACK_APPLY_SUPPORTER:
        await log(context, "User chose apply supporter from menu", user=user)
        await telemetry.track_event(context, "apply_supporter_clicked", user=user)
        await query.message.reply_text("מתחילים בהרשמת תומך. איך קוראים לך?")
        return SUPPORTER_NAME

    if data == CALLBACK_APPLY_EXPERT:
        await log(context, "User chose apply expert from menu", user=user)
        await telemetry.track_event(context, "apply_expert_clicked", user=user)
        await query.message.reply_text("מתחילים בהגשת מועמדות כמומחה. מה שמך המלא?")
        return EXPERT_NAME

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

    await admin_handlers.handle_admin_callback(query, context)
    return ConversationHandler.END
