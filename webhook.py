from telegram.ext import Application
from handlers.registration import register_handler
from handlers.admin import approve_handler
from handlers.experts import expert_handler
from handlers.images import image_handler, resize_handler
from handlers.help_all import all_handler
import os

def start_webhook():
    app = Application.builder().token(
        os.getenv("TELEGRAM_BOT_TOKEN")
    ).build()

    app.add_handler(register_handler)
    app.add_handler(approve_handler)
    app.add_handler(expert_handler)
    app.add_handler(image_handler)
    app.add_handler(resize_handler)
    app.add_handler(all_handler)

    app.run_polling()
