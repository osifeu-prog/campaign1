# bot/handlers/image_handlers.py
# ==========================================
# טיפול בתמונות / GIF – המרה, דחיסה, resize
# ==========================================

import os
import tempfile

from telegram import Update
from telegram.ext import ContextTypes

from bot.core.media_utils import resize_image, resize_gif, cleanup_files
from utils.constants import IMAGE_SIZES, TEMP_MEDIA_DIR
from services.logger_service import log


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]

    file = await photo.get_file()
    temp_dir = tempfile.mkdtemp(dir=TEMP_MEDIA_DIR)
    input_path = os.path.join(temp_dir, "input.jpg")
    await file.download_to_drive(input_path)

    out_paths = resize_image(input_path, temp_dir, IMAGE_SIZES)

    await update.message.reply_text("📸 התמונה עובדה בהצלחה.")
    await log(context, "Photo processed", user=user)

    cleanup_files([temp_dir])


async def handle_animation_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    anim = update.message.animation or update.message.document

    file = await anim.get_file()
    temp_dir = tempfile.mkdtemp(dir=TEMP_MEDIA_DIR)
    input_path = os.path.join(temp_dir, "input.gif")
    await file.download_to_drive(input_path)

    out_paths = resize_gif(input_path, temp_dir, IMAGE_SIZES)

    await update.message.reply_text("🎞️ האנימציה עובדה בהצלחה.")
    await log(context, "GIF processed", user=user)

    cleanup_files([temp_dir])
