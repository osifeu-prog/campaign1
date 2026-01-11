# ===============================
# start_flow – /start, קרוסלה, סוציוקרטיה, סיום
# ===============================

import os
import random
from typing import List

from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes

from bot.core.session_manager import session_manager
from bot.core.telemetry import telemetry
from bot.core.rate_limiter import rate_limiter
from bot.core.locale_service import locale_service
from bot.ui.keyboards import build_start_keyboard, build_start_carousel_keyboard
from services.logger_service import log
from utils.constants import (
    START_IMAGES_DIR,
    CALLBACK_START_SLIDE,
    CALLBACK_START_SOCI,
    CALLBACK_START_FINISH,
)


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


def get_intro_slides() -> List[str]:
    slides: List[str] = []

    slides.append(
        "הגיע הזמן לשינוי אמיתי\n"
        "ישראל שלנו זקוקה למהפכה - לא של כעס, אלא של אהבה ומקצועיות.\n"
        "אנחנו, תנועת אחדות, מציעים חלופה אמיתית:\n\n"
        "• 120 מומחים בתחומם במקום 120 פוליטיקאים\n"
        "• מבנה סוציוקרטי שמעמיד את האזרח במרכז\n"
        "• פתרונות מקצועיים במקום משחקי כוח"
    )

    slides.append(
        "💡 מי יכול להצטרף לתנועה?\n"
        "אנחנו מגייסים שלוש קבוצות:\n"
        "1️⃣ מומחים/מתמודדים – אנשי מקצוע שרוצים להוביל שינוי מבפנים.\n"
        "2️⃣ פעילים – אזרחים שרוצים לקחת חלק פעיל בשינוי.\n"
        "3️⃣ תומכים ומצביעים – כל מי שמאמין בדרך החדשה.\n\n"
        "העיקרון שלנו:\n"
        "לא הון, לא שלטון, לא עולם תחתון – אלא תרומה אמיתית לקהילה דרך מקצועיות ומומחיות."
    )

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


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if not rate_limiter.allow(user.id, "start", limit=5, per_seconds=60):
        await update.message.reply_text("ביצעת יותר מדי פעולות בזמן קצר. נסה שוב עוד דקה.")
        return

    start_param = ""
    if update.message and update.message.text.startswith("/start"):
        parts = update.message.text.split(" ", maxsplit=1)
        if len(parts) == 2:
            start_param = parts[1].strip()

    session = session_manager.get_or_create(user, start_param=start_param)
    context.user_data["user_id"] = session.user_id
    context.user_data["username"] = session.username
    context.user_data["full_name_telegram"] = session.full_name
    context.user_data.setdefault("created_at", session.created_at)
    context.user_data["start_param"] = start_param

    lang = locale_service.detect_language(user.language_code)
    await log(context, "/start called", user=user, extra={"start_param": start_param})
    await telemetry.track_event(context, "start_invoked", user=user, properties={"start_param": start_param})

    slides = get_intro_slides()
    first_text = slides[0]
    image_path = _get_random_start_image()

    if image_path:
        with open(image_path, "rb") as f:
            msg = await context.bot.send_photo(
                chat_id=chat.id,
                photo=f,
                caption=first_text,
                reply_markup=build_start_carousel_keyboard(slide_index=0, total_slides=len(slides)),
            )
    else:
        msg = await update.message.reply_text(
            first_text,
            reply_markup=build_start_carousel_keyboard(slide_index=0, total_slides=len(slides)),
        )

    session_manager.update_state(
        user_id=user.id,
        flow="start_carousel",
        state="slide_0",
        message_id=msg.message_id,
        metadata={"language": lang},
    )


async def handle_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    slides = get_intro_slides()
    total = len(slides)

    if data.startswith(f"{CALLBACK_START_SLIDE}:"):
        _, idx_str = data.split(":", 1)
        idx = int(idx_str)
        idx = max(0, min(idx, total - 1))

        image_path = _get_random_start_image()
        text = slides[idx]

        if query.message.photo:
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

        session_manager.update_state(
            user_id=user.id,
            flow="start_carousel",
            state=f"slide_{idx}",
            message_id=query.message.message_id,
        )
        await telemetry.track_event(context, "start_slide_view", user=user, properties={"slide_index": idx})
        return

    if data == CALLBACK_START_SOCI:
        text = get_sociocracy_text()
        await query.message.reply_text(text)
        await telemetry.track_event(context, "sociocracy_opened", user=user)
        return

    if data == CALLBACK_START_FINISH:
        await send_final_start_message(update, context)
        session_manager.update_state(
            user_id=user.id,
            flow="start_finish",
            state="shown",
        )
        await telemetry.track_event(context, "start_finish", user=user)
        return


async def send_final_start_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = locale_service.detect_language(user.language_code)
    text = locale_service.t("start_intro", lang=lang)

    keyboard = build_start_keyboard()

    if update.callback_query:
        msg = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
    else:
        msg = await update.message.reply_text(text, reply_markup=keyboard)

    session_manager.update_state(
        user_id=user.id,
        flow="start_intro",
        state="shown",
        message_id=msg.message_id,
    )
