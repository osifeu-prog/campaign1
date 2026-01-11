# bot/handlers/image_handlers.py
import os
import tempfile
import asyncio
from typing import List, Tuple, Dict, Any

from telegram import Update, InputFile
from telegram.ext import ContextTypes, Job

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

# --- Job functions (run in JobQueue) ---

async def _process_photo_job(context: ContextTypes.DEFAULT_TYPE):
    """
    JobQueue job: downloads the photo, resizes to IMAGE_SIZES and sends back to chat.
    Expects context.job.data = {"file_id": str, "chat_id": int, "user_id": int}
    """
    data: Dict[str, Any] = context.job.data or {}
    file_id = data.get("file_id")
    chat_id = data.get("chat_id")
    user_id = data.get("user_id")
    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp(dir=TEMP_MEDIA_DIR)
        in_path = os.path.join(tmp_dir, f"{file_id}.jpg")
        await _download_file(context.bot, file_id, in_path)

        out_paths = resize_image(in_path, tmp_dir, IMAGE_SIZES)

        # send resized images sequentially (could be sent as album if desired)
        for p in out_paths:
            try:
                await context.bot.send_photo(chat_id=chat_id, photo=InputFile(p))
            except Exception:
                # continue sending others even if one fails
                continue

        # log
        try:
            await log(context, "Processed photo (background job) and returned sizes", user=context.application.bot.get_chat(user_id), extra={"sizes": [f"{w}x{h}" for w,h in IMAGE_SIZES]})
        except Exception:
            # best-effort logging without failing the job
            await log(context, "Processed photo (background job) and returned sizes", extra={"sizes": [f"{w}x{h}" for w,h in IMAGE_SIZES]})
    except Exception as e:
        await log(context, f"Error in photo job: {e}", level="ERROR")
    finally:
        if tmp_dir:
            try:
                cleanup_files([tmp_dir])
            except Exception:
                pass

async def _process_animation_job(context: ContextTypes.DEFAULT_TYPE):
    """
    JobQueue job: downloads animation (GIF/MP4), resizes and sends back.
    Expects context.job.data = {"file_id": str, "chat_id": int, "user_id": int}
    """
    data: Dict[str, Any] = context.job.data or {}
    file_id = data.get("file_id")
    chat_id = data.get("chat_id")
    user_id = data.get("user_id")
    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp(dir=TEMP_MEDIA_DIR)
        in_path = os.path.join(tmp_dir, f"{file_id}.gif")
        await _download_file(context.bot, file_id, in_path)

        out_paths = resize_gif(in_path, tmp_dir, IMAGE_SIZES)

        for p in out_paths:
            try:
                await context.bot.send_animation(chat_id=chat_id, animation=InputFile(p))
            except Exception:
                continue

        try:
            await log(context, "Processed animation (background job) and returned sizes", user=context.application.bot.get_chat(user_id), extra={"sizes": [f"{w}x{h}" for w,h in IMAGE_SIZES]})
        except Exception:
            await log(context, "Processed animation (background job) and returned sizes", extra={"sizes": [f"{w}x{h}" for w,h in IMAGE_SIZES]})
    except Exception as e:
        await log(context, f"Error in animation job: {e}", level="ERROR")
    finally:
        if tmp_dir:
            try:
                cleanup_files([tmp_dir])
            except Exception:
                pass

# --- Handlers that enqueue jobs ---

async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Enqueue a background job to process a photo.
    """
    user = update.effective_user
    try:
        photos = update.message.photo
        if not photos:
            return
        file_obj = photos[-1]
        file_id = file_obj.file_id

        # Optional: check file size / limits (best-effort; Telegram file size may require fetching file metadata)
        # Enqueue job
        job_data = {"file_id": file_id, "chat_id": update.effective_chat.id, "user_id": user.id}
        # schedule immediate job
        try:
            context.application.job_queue.run_once(_process_photo_job, when=0, data=job_data)
            await update.message.reply_text("הקובץ התקבל. מעבד ברקע — אשלח את הגרסאות המוקטנות כשיהיו מוכנות.")
            await log(context, "Enqueued photo processing job", user=user, extra={"file_id": file_id})
        except Exception as e:
            # fallback: try synchronous processing if job queue unavailable
            await log(context, f"Failed to enqueue photo job: {e}", user=user, level="WARNING")
            # attempt direct processing (best-effort)
            await _process_photo_job(context)
    except Exception as e:
        await log(context, f"Error enqueueing photo job: {e}", user=user, level="ERROR")

async def handle_animation_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Enqueue a background job to process an animation (GIF/MP4).
    """
    user = update.effective_user
    try:
        anim = update.message.animation or update.message.document
        if not anim:
            return
        file_id = anim.file_id

        job_data = {"file_id": file_id, "chat_id": update.effective_chat.id, "user_id": user.id}
        try:
            context.application.job_queue.run_once(_process_animation_job, when=0, data=job_data)
            await update.message.reply_text("הקובץ התקבל. מעבד ברקע — אשלח את הגרסאות המוקטנות כשיהיו מוכנות.")
            await log(context, "Enqueued animation processing job", user=user, extra={"file_id": file_id})
        except Exception as e:
            await log(context, f"Failed to enqueue animation job: {e}", user=user, level="WARNING")
            await _process_animation_job(context)
    except Exception as e:
        await log(context, f"Error enqueueing animation job: {e}", user=user, level="ERROR")
