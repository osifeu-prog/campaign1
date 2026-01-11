from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters
from PIL import Image
import os

ALLOWED_RESOLUTIONS = {
    "640x360": (640, 360),
    "320x180": (320, 180),
    "960x540": (960, 540)
}

async def image_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    path = f"/tmp/{photo.file_id}.jpg"
    await file.download_to_drive(path)

    context.user_data["image_path"] = path

    keyboard = [
        [InlineKeyboardButton(r, callback_data=r)]
        for r in ALLOWED_RESOLUTIONS
    ]

    await update.message.reply_text(
        "בחר רזולוציה:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
  async def resize_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    size = ALLOWED_RESOLUTIONS[query.data]
    path = context.user_data["image_path"]

    img = Image.open(path)
    img = img.resize(size)

    new_path = path.replace(".jpg", f"_{query.data}.jpg")
    img.save(new_path)

    await query.message.reply_photo(open(new_path, "rb"))

image_handler = MessageHandler(filters.PHOTO, image_received)
resize_handler = CallbackQueryHandler(resize_callback)
