from telegram.ext import MessageHandler, filters, ContextTypes
from telegram import Update
from core.permissions import has_permission
from core.images import resize_image

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not has_permission(user.id):
        await update.message.reply_text("אין לך הרשאה. שלח /request_image_access")
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    path = f"/tmp/{user.id}.jpg"
    await file.download_to_drive(path)

    out = resize_image(path, (640,360))
    await update.message.reply_photo(photo=open(out, "rb"))

image_message_handler = MessageHandler(filters.PHOTO, handle_image)
