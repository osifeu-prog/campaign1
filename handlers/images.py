from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters
from PIL import Image
import os

ALLOWED_RESOLUTIONS = {
    "640x360": (640, 360),
    "320x180": (320, 180),
    "960x540": (960, 540),
}

async def image_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()

    path = f"/tmp/{photo.file_id}.jpg"
    await file.download_to_drive(path)

    context.user_data["image_path"] = path

    keyboard = [
        [InlineKeyboardButton(text=key, callback_data=key)]
        for key in ALLOWED_RESOLUTIONS.keys()
    ]

    await update.message.reply_text(
        "בחר רזולוציה לתמונה:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def resize_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data not in ALLOWED_RESOLUTIONS:
        await query.message.reply_text("רזולוציה לא חוקית")
        return

    size = ALLOWED_RESOLUTIONS[query.data]
    path = context.user_data.get("image_path")

    if not path or not os.path.exists(path):
        await query.message.reply_text("לא נמצאה תמונה לעיבוד")
        return

    img = Image.open(path)
    img = img.resize(size)

    new_path = path.replace(".jpg", f"_{query.data}.jpg")
    img.save(new_path)

    await query.message.reply_photo(photo=open(new_path, "rb"))

image_handler = MessageHandler(filters.PHOTO, image_received)
resize_handler = CallbackQueryHandler(resize_callback)
