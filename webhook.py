import os
from telegram.ext import Application
from handlers.start import start_handler
from handlers.help_all import all_handler

def start_webhook():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(token).build()
    app.add_handler(start_handler)
    app.add_handler(all_handler)
    app.run_polling()
