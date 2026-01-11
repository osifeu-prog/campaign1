from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from core.slides import get_slide, slides_count

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["slide"] = 0
    await send_slide(update, context)

async def send_slide(update, context):
    i = context.user_data["slide"]
    image, text = get_slide(i)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️", callback_data="prev"),
            InlineKeyboardButton("➡️", callback_data="next")
        ]
    ])

    if update.message:
        await update.message.reply_photo(
            photo=open(image, "rb"),
            caption=text,
            reply_markup=keyboard
        )
    else:
        await update.callback_query.message.edit_media(
            media={
                "type": "photo",
                "media": open(image, "rb"),
                "caption": text
            },
            reply_markup=keyboard
        )

async def slide_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    max_i = slides_count() - 1

    if q.data == "next":
        context.user_data["slide"] = min(context.user_data["slide"] + 1, max_i)
    else:
        context.user_data["slide"] = max(context.user_data["slide"] - 1, 0)

    await send_slide(update, context)

start_handler = CommandHandler("start", start)
slides_handler = CallbackQueryHandler(slide_nav, pattern="^(next|prev)$")
