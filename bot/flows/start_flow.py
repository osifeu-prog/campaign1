# bot/flows/start_flow.py
# ===============================
# start_flow – /start, קרוסלה, סוציוקרטיה, סיום
# ===============================

import os
from typing import List

from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes

from bot.core.session_manager import session_manager
from bot.core.telemetry import telemetry
from bot.core.rate_limiter import rate_limiter
from bot.core.locale_service import locale_service
from bot.ui.keyboards import (
    build_start_keyboard,
    build_start_carousel_keyboard,
)
from services.logger_service import log
from utils.constants import (
    START_IMAGES_DIR,
    CALLBACK_START_SLIDE,
    CALLBACK_START_SOCI,
    CALLBACK_START_FINISH,
)


# ===============================
# Helper: load images
# ===============================

def _get_start_images() -> List[str]:
    if not os.path.isdir(START_IMAGES_DIR):
        return []
    files = [
        os.path.join(START_IMAGES_DIR, f)
        for f in os.listdir(START_IMAGES_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    files.sort()
    return files


# ===============================
# /start command
# ===============================

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = locale_service.detect_language(user.language_code)
    session_manager.get_or_create(user)

    # Rate limit: prevent spam
    if not rate_limiter.allow(user.id, "start", limit=3, per_seconds=10):
        await update.message.reply_text("אנא המתן מספר שניות ונסה שוב.")
        return

    await log(context, "Start command", user=user)

    images = _get_start_images()
    if not images:
        await update.message.reply_text(locale_service.t("start_intro", lang))
        return

    # First slide
    await update.message.reply_photo(
        photo=open(images[0], "rb"),
        caption=locale_service.t("start_intro", lang),
        reply_markup=build_start_carousel_keyboard(0, len(images)),
    )


# ===============================
# Carousel navigation
# ===============================

async def handle_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    user = query.from_user
    images = _get_start_images()
    total = len(images)

    if data.startswith(f"{CALLBACK_START_SLIDE}:"):
        _, idx_str = data.split(":", 1)
        idx = int(idx_str)

        if idx < 0:
            idx = 0
        if idx >= total:
            idx = total - 1

        await query.message.edit_media(
            media=InputMediaPhoto(open(images[idx], "rb")),
            reply_markup=build_start_carousel_keyboard(idx, total),
        )
        return

    if data == CALLBACK_START_SOCI:
        await query.message.reply_text(
            "סוציוקרטיה (Sociocracy) היא שיטת ממשל המבוססת על שוויון, שקיפות והשתתפות של כל חברי הקהילה.\n\n"
            "היא מאפשרת קבלת החלטות איכותית, שקופה, ללא משחקי כוח.\n\n"
            "רוצה לדעת איך זה עובד בפועל?",
            reply_markup=build_start_keyboard(),
        )
        return

    if data == CALLBACK_START_FINISH:
        await telemetry.track_event(context, "start_finish", user=user)
        await query.message.reply_text(
            "ברוך הבא לתנועת אחדות.\n\n"
            "איך תרצה להצטרף?",
            reply_markup=build_start_keyboard(),
        )
        return
