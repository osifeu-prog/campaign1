# ===============================
# bot_handlers – Router ראשי
# ===============================

import os
import random
from datetime import datetime
from typing import List, Tuple

from telegram import Update, InputMediaPhoto
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot.states import (
    CHOOSING_ROLE,
    SUPPORTER_NAME,
    SUPPORTER_CITY,
    SUPPORTER_EMAIL,
    SUPPORTER_PHONE,
    SUPPORTER_FEEDBACK,
    EXPERT_NAME,
    EXPERT_FIELD,
    EXPERT_EXPERIENCE,
    EXPERT_POSITION,
    EXPERT_LINKS,
    EXPERT_WHY,
)
from bot import supporter_handlers, expert_handlers
from bot.keyboards import (
    build_start_keyboard,
    build_main_menu_for_user,
    build_start_carousel_keyboard,
)
from services import sheets_service
from services.logger_service import log
from utils.constants import (
    ADMIN_IDS,
    ROLE_SUPPORTER,
    ROLE_EXPERT,
    START_IMAGES_DIR,
    CALLBACK_MENU_MAIN,
    CALLBACK_MENU_SUPPORT,
    CALLBACK_MENU_EXPERT,
    CALLBACK_MENU_ADMIN,
    CALLBACK_APPLY_SUPPORTER,
    CALLBACK_APPLY_EXPERT,
    CALLBACK_MENU_POSITIONS,
    CALLBACK_START_SLIDE,
    CALLBACK_START_SOCI,
    CALLBACK_START_SOCI_BACK,
    CALLBACK_START_FINISH,
)


# ===============================
# עזר: בדיקת אדמין
# ===============================

def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS


# ===============================
# עזר: טעינת תמונות לתיקיית הפתיחה
# ===============================

def _get_start_images() -> List[str]:
    if not os.path.isdir(START_IMAGES_DIR):
        return []
    files = [
        os.path.join(START_IMAGES_DIR, f)
        for f in os.listdir(START_IMAGES_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ]
    return files


def _get_random_start_image() -> str | None:
    imgs = _get_start_images()
    if not imgs:
        return None
    return random.choice(imgs)


# ===============================
# טקסטים לשקופיות הפתיחה
# ===============================

def get_intro_slides() -> List[str]:
    slides: List[str] = []

    # הודעה 1 - פתיחה וחזון
    slides.append(
        "הגיע הזמן לשינוי אמיתי\n"
        "ישראל שלנו זקוקה למהפכה - לא של כעס, אלא של אהבה ומקצועיות.\n"
        "אנחנו, תנועת אחדות, מציעים חלופה אמיתית:\n\n"
        "• 120 מומחים בתחומם במקום 120 פוליטיקאים\n"
        "• מבנה סוציוקרטי שמעמיד את האזרח במרכז\n"
        "• פתרונות מקצועיים במקום משחקי כוח"
    )

    # הודעה 2 - מי אנחנו מחפשים
    slides.append(
        "💡 מי יכול להצטרף לתנועה?\n"
        "אנחנו מגייסים שלוש קבוצות:\n"
        "1️⃣ מומחים/מתמודדים – אנשי מקצוע שרוצים להוביל שינוי מבפנים.\n"
        "2️⃣ פעילים – אזרחים שרוצים לקחת חלק פעיל בשינוי.\n"
        "3️⃣ תומכים ומצביעים – כל מי שמאמין בדרך החדשה.\n\n"
        "העיקרון שלנו:\n"
        "לא הון, לא שלטון, לא עולם תחתון – אלא תרומה אמיתית לקהילה דרך מקצועיות ומומחיות."
    )

    # הודעה 3 - החזון המעשי
    slides.append(
        "🎯 איך זה יעבוד בפועל?\n"
        "במקום פלוגה מפולגת – תנועה מאוחדת.\n"
        "במקום משחקים פוליטיים – צוות ניהול מקצועי.\n"
        "במקום הבטחות ריקות – פתרונות ממשיים.\n\n"
        "אנחנו בונים:\n"
        "✅ שקיפות מלאה\n"
        "✅ מבנה סוציוקרטי שמאפשר השפעה אמיתית לכל אזרח\n"
        "✅ 120 אנשים שעומדים במילה שלהם ופועלים למען המדינה, לא למען עצמם."
    )

    # הודעה 4 - קריאה לפעולה
    slides.append(
        "📝 הצטרפו עכשיו לתנועת אחדות\n\n"
        "תהליך ההרשמה פשוט ושקוף:\n"
        "1️⃣ מלאו את פרטיכם בטופס ההרשמה\n"
        "2️⃣ כל הרשמה מתועדת אוטומטית ב-Google Sheets\n"
        "3️⃣ המידע זמין לכל מי שמבקש לראותו - שקיפות מלאה\n"
        "4️⃣ נציג מהתנועה יצור איתכם קשר להמשך\n\n"
        "זה הזמן לעשות את ההבדל.\n"
        "ישראל זקוקה למומחים שלה, לא לפוליטיקאים שלה."
    )

    # הודעה 5 - סיום ועידוד
    slides.append(
        "🌟 יחד ניצור את השינוי\n\n"
        "כל תנועה גדולה מתחילה בצעד אחד.\n"
        "כל מהפכה מתחילה באדם אחד שאומר 'די'.\n\n"
        "הצטרפו לתנועת אחדות והיו חלק מהדור שישנה את פני המדינה.\n"
        "לא דרך אלימות. לא דרך שנאה.\n"
        "אלא דרך מקצועיות, מומחיות, ואהבת ישראל.\n\n"
        "120 מקומות. מיליוני אזרחים. חזון אחד.\n"
        "💪 ביחד נצליח"
    )

    return slides


def get_sociocracy_text() -> str:
    return (
        "סוציוקרטיה (Sociocracy) היא שיטת ממשל וקבלת החלטות המבוססת על שוויון, שקיפות והשתתפות של כל חברי הארגון או הקהילה.\n"
        "השם מורכב מ-socius (לטינית: 'חברים') ו-kratein (יוונית: 'ניהול') – כלומר 'ניהול החברים' או 'אחזקה של שווים'.\n\n"
        "יתרונות הסוציוקרטיה:\n\n"
        "1. קבלת החלטות בהסכמה (Consent)\n"
        "• החלטות מתקבלות לא ברוב, אלא כשאין התנגדות מבוססת.\n"
        "• כל אדם יכול להעלות התנגדות רק אם ההחלטה תפגע ביכולתו לתרום למטרה המשותפת.\n"
        "• זה לא פה אחד – אלא: 'אין לי סיבה מספיק חשובה להתנגד'.\n\n"
        "2. ארגון במעגלים (Circles)\n"
        "• הארגון מחולק למעגלים לפי תפקידים ותחומי אחריות.\n"
        "• כל מעגל אוטונומי בתחום שלו.\n"
        "• המעגלים מחוברים זה לזה בהיררכיה שטוחה יותר.\n\n"
        "3. קישור כפול (Double Linking)\n"
        "• כל מעגל מחובר למעגל שמעליו דרך שני נציגים:\n"
        "  – מנהיג שנבחר מלמעלה בבחירות שקופות (מנומקות).\n"
        "  – נציג שנבחר מלמטה בבחירות שקופות (מנומקות).\n"
        "• זה מבטיח זרימת מידע דו-כיוונית ומאזן כוחות.\n\n"
        "4. בחירות פתוחות\n"
        "• תפקידים מתמלאים בתהליך בחירות שקוף.\n"
        "• כל אחד מסביר למה הוא ממליץ על מועמד מסוים.\n"
        "• הבחירה היא בהסכמה, לא בהצבעה סודית.\n\n"
        "4.1 איך זה עובד בפועל? (דוגמה: תקציב)\n"
        "• מציגים את ההצעה לכולם.\n"
        "• שואלים שאלות הבהרה.\n"
        "• כל אחד מביע את דעתו.\n"
        "• משכללים את ההצעה.\n"
        "• שואלים: 'האם יש למישהו התנגדות מבוססת?'\n"
        "• אם יש – עובדים יחד לשכלל את ההצעה.\n"
        "• אם אין – ההחלטה מתקבלת.\n\n"
        "4.3 היתרונות\n"
        "✅ החלטות איכותיות יותר – כי כל הקולות נשמעים.\n"
        "✅ מחויבות גבוהה יותר – כי כולם חלק מההחלטה.\n"
        "✅ פחות קונפליקטים – אין 'מנצחים ומפסידים'.\n"
        "✅ שקיפות מלאה.\n"
        "✅ גמישות – קל לשנות החלטות כשהן לא עובדות.\n"
        "✅ העצמה – כל אדם יכול להשפיע באמת.\n\n"
        "4.4 האתגרים\n"
        "⚠️ לוקח יותר זמן בהתחלה.\n"
        "⚠️ דורש חינוך והכשרה.\n"
        "⚠️ לא תמיד מתאים לכל תרבות.\n"
        "⚠️ בקנה מידה גדול – צריך מבנה מחושב היטב.\n\n"
        "5. סוציוקרטיה במדינה – איך זה יכול לעבוד?\n"
        "• במקום 120 חברי כנסת – מעגלים תחומיים (בריאות, חינוך, ביטחון, כלכלה וכו').\n"
        "• מומחים בכל מעגל שמקבלים החלטות בתחום שלהם.\n"
        "• קישור בין המעגלים דרך נציגים דו-כיווניים.\n"
        "• החלטות לאומיות גדולות מתקבלות בהסכמה של כל המעגלים.\n"
        "• שקיפות מלאה – כל אזרח יכול לראות את התהליכים.\n\n"
        "סוציוקרטיה היא ניסיון ליצור 'דמוקרטיה משופרת' – שבה כל אדם באמת משפיע, והחלטות מתקבלות על סמך חוכמה קולקטיבית ולא משחקי כוח פוליטיים."
    )


# ===============================
# /start – פתיחה + קרוסלה + סוציוקרטיה
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # הכנת user_data בסיסי
    context.user_data["user_id"] = user.id
    context.user_data["username"] = user.username or ""
    context.user_data["full_name_telegram"] = user.full_name
    context.user_data.setdefault("created_at", datetime.utcnow().isoformat())

    await log(context, "/start called", user=user)

    slides = get_intro_slides()
    first_text = slides[0]
    image_path = _get_random_start_image()

    if image_path:
        with open(image_path, "rb") as f:
            await context.bot.send_photo(
                chat_id=chat.id,
                photo=f,
                caption=first_text,
                reply_markup=build_start_carousel_keyboard(slide_index=0, total_slides=len(slides)),
            )
    else:
        await update.message.reply_text(
            first_text,
            reply_markup=build_start_carousel_keyboard(slide_index=0, total_slides=len(slides)),
        )


async def handle_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    slides = get_intro_slides()
    total = len(slides)

    # start_slide:<index>
    if data.startswith(f"{CALLBACK_START_SLIDE}:"):
        _, idx_str = data.split(":", 1)
        idx = int(idx_str)
        idx = max(0, min(idx, total - 1))

        image_path = _get_random_start_image()
        text = slides[idx]

        if query.message.photo:
            # עריכת הודעה קיימת (קרוסלה)
            if image_path:
                with open(image_path, "rb") as f:
                    await query.message.edit_media(
                        media=InputMediaPhoto(media=f, caption=text),
                        reply_markup=build_start_carousel_keyboard(idx, total),
                    )
            else:
                await query.message.edit_caption(
                    caption=text,
                    reply_markup=build_start_carousel_keyboard(idx, total),
                )
        else:
            if image_path:
                with open(image_path, "rb") as f:
                    await query.message.edit_media(
                        media=InputMediaPhoto(media=f, caption=text),
                        reply_markup=build_start_carousel_keyboard(idx, total),
                    )
            else:
                await query.message.edit_text(
                    text=text,
                    reply_markup=build_start_carousel_keyboard(idx, total),
                )

    elif data == CALLBACK_START_SOCI:
        text = get_sociocracy_text()
        keyboard = build_start_carousel_keyboard(slide_index=0, total_slides=total)
        # נשלח כהודעה חדשה, לא נדרוס את הקרוסלה
        await query.message.reply_text(text)
        await query.message.reply_text(
            "אפשר לחזור לשקופיות על ידי לחיצה על 'המשך' או 'סיום והצטרפות' בקרוסלה.",
            reply_markup=keyboard,
        )

    elif data == CALLBACK_START_FINISH:
        # כאן נציג את ההודעה הסופית + תפריט / הרשמה
        await send_final_start_message(update, context)


async def send_final_start_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    text = (
        "ברוך הבא לתנועת אחדות.\n\n"
        "אני הבוט שדרכו מצטרפים, נרשמים כתומכים ומגישים מועמדות כמומחים.\n\n"
        "איך תרצה להצטרף?"
    )

    keyboard = build_start_keyboard()

    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

    await log(context, "Final start message shown", user=user)


# ===============================
# פקודות כלליות
# ===============================

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_admin_flag = is_admin(user.id)

    keyboard = build_main_menu_for_user(user.id, is_admin_flag)
    await update.message.reply_text("📋 תפריט ראשי", reply_markup=keyboard)


async def all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start – התחלה מחדש\n"
        "/menu – פתיחת תפריט ראשי\n"
        "/help – רשימת פקודות\n"
        "/myid – הצגת ה־user_id שלך\n"
        "/groupid – הצגת group id (בקבוצה)\n"
    )
    await update.message.reply_text(text)


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"user_id שלך: {user_id}")


async def group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await update.message.reply_text(f"group/chat id: {chat.id}")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("הפקודה הזו לא מוכרת. נסה /help.")


# ===============================
# תפריטי callback (menu)
# ===============================

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    if data == "expert":
        # התחלת רישום מומחה
        await query.message.reply_text("מעולה, נתחיל בתהליך הגשת מועמדות כמומחה. מה שמך המלא?")
        return EXPERT_NAME

    if data == "supporter":
        # התחלת רישום תומך
        await query.message.reply_text("נשמח להכיר! איך קוראים לך?")
        return SUPPORTER_NAME

    if data == CALLBACK_MENU_MAIN:
        keyboard = build_main_menu_for_user(user.id, is_admin(user.id))
        await query.message.reply_text("📋 תפריט ראשי", reply_markup=keyboard)
        return ConversationHandler.END

    # תפריטי תומך / מומחה / אדמין – כאן תוכל להרחיב לפי מה שכבר קיים אצלך
    if data == CALLBACK_MENU_SUPPORT:
        await query.message.reply_text("תפריט תומך – בהמשך אפשר להציג פרופיל, קישור אישי ועוד.")
        return ConversationHandler.END

    if data == CALLBACK_MENU_EXPERT:
        await query.message.reply_text("פאנל מומחה – בהמשך אפשר להציג סטטוס, מקום, קישור מומחה ועוד.")
        return ConversationHandler.END

    if data == CALLBACK_MENU_ADMIN:
        from bot.keyboards import build_admin_panel_keyboard
        await query.message.reply_text("🛠️ פאנל אדמין", reply_markup=build_admin_panel_keyboard())
        return ConversationHandler.END

    if data == CALLBACK_APPLY_SUPPORTER:
        await query.message.reply_text("נרשום אותך כתומך. איך קוראים לך?")
        return SUPPORTER_NAME

    if data == CALLBACK_APPLY_EXPERT:
        await query.message.reply_text("נתחיל מחדש את תהליך המומחה. מה שמך המלא?")
        return EXPERT_NAME

    return ConversationHandler.END


# ===============================
# ConversationHandler הראשי
# ===============================

def get_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[],
        states={
            SUPPORTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_handlers.supporter_name)],
            SUPPORTER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_handlers.supporter_city)],
            SUPPORTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_handlers.supporter_email)],
            SUPPORTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_handlers.supporter_phone)],
            SUPPORTER_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, supporter_handlers.supporter_feedback)],

            EXPERT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_name)],
            EXPERT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_field)],
            EXPERT_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_experience)],
            EXPERT_POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_position)],
            EXPERT_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_links)],
            EXPERT_WHY: [MessageHandler(filters.TEXT & ~filters.COMMAND, expert_handlers.expert_why)],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("menu", menu_command),
        ],
    )
