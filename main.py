from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler
import config
import bot_handlers

app = Flask(__name__)

application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
application.add_handler(CommandHandler("start", bot_handlers.start))

@app.post("/webhook")
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
