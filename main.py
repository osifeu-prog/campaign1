from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler
import os
import bot_handlers

# Load environment variables from Railway
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
USERS_SHEET_NAME = os.getenv("USERS_SHEET_NAME")
EXPERTS_SHEET_NAME = os.getenv("EXPERTS_SHEET_NAME")

app = Flask(__name__)

# Initialize Telegram bot
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Register handlers
application.add_handler(CommandHandler("start", bot_handlers.start))

@app.post("/webhook")
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
