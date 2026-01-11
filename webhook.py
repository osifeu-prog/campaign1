import os
from telegram.ext import Application
from handlers.start import start_handler
from handlers.help_all import all_handler
from handlers.image_resize import image_message_handler
from handlers.image_permission import permission_request_handler

def start_app():
    app = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()

    app.add_handler(start_handler)
    app.add_handler(all_handler)
    app.add_handler(permission_request_handler)
    app.add_handler(image_message_handler)

    app.run_polling()
