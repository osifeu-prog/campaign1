# bot/handlers/image_handlers.py
import os
import tempfile
import asyncio
from typing import List, Tuple

from telegram import Update, InputFile
from telegram.ext import ContextTypes

from utils.constants import (
    IMAGE_SIZES,
    TEMP_MEDIA_DIR,
    MAX_GIF_DURATION_SECONDS,
    MAX_MEDIA_FILESIZE_MB,
)
from bot.core.media_utils import resize_image, resize_gif, cleanup_files
from services.logger_service import log

# Ensure temp dir
os.makedirs(TEMP_MEDIA_DIR, exist_ok=True)

async def _download_file(bot, file_id: str, dest_path: str):
    f = await bot.get_file(file_id)
    await f.download_to_drive(dest_path)
    return dest_path

async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles incoming photos (static images). Creates resized versions and sends them back.
    """
    user = update.effective_user
    try:
        photos = update.message.photo
        if not photos:
            return
        # choose largest
        file_obj = photos[-1]
        file_id = file_obj.file_id

        tmp_dir = tempfile.mkdtemp(dir=TEMP_MEDIA_DIR)
        in_path = os.path.join(tmp_dir, f"{file_id}.jpg")
        await _download_file(context.bot, file_id, in_path)

        # resize
        sizes = IMAGE_SIZES
        out_paths = resize_image(in_path, tmp_dir, sizes)

        # send as album
        media_group = []
        for p in out_paths:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(p))
        await log(context, "Processed photo and returned sizes", user=user, extra={"sizes": [f"{w}x{h}" for w,h in sizes]})
    except Exception as e:
        await log(context, f"Error processing photo: {e}", user=user, level="ERROR")
    finally:
        try:
            cleanup_files([tmp_dir])
        except Exception:
            pass

async def handle_animation_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles animations (GIF/MP4). Resizes and returns animations.
    """
    user = update.effective_user
    try:
        anim = update.message.animation or update.message.document
        if not anim:
            return
        file_id = anim.file_id
        tmp_dir = tempfile.mkdtemp(dir=TEMP_MEDIA_DIR)
        in_path = os.path.join(tmp_dir, f"{file_id}.gif")
        await _download_file(context.bot, file_id, in_path)

        sizes = IMAGE_SIZES
        out_paths = resize_gif(in_path, tmp_dir, sizes)

        for p in out_paths:
            await context.bot.send_animation(chat_id=update.effective_chat.id, animation=InputFile(p))
        await log(context, "Processed animation and returned sizes", user=user, extra={"sizes": [f"{w}x{h}" for w,h in sizes]})
    except Exception as e:
        await log(context, f"Error processing animation: {e}", user=user, level="ERROR")
    finally:
        try:
            cleanup_files([tmp_dir])
        except Exception:
            pass
