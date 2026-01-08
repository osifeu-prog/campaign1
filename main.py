from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler
import os
import asyncio
import threading
import bot_handlers

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = Flask(__name__)

# Create application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Register handlers
application.add_handler(CommandHandler("start", bot_handlers.start))

# Create a dedicated event loop for PTB
ptb_loop = asyncio.new_event_loop()

def run_ptb():
    asyncio.set_event_loop(ptb_loop)
    ptb_loop.run_until_complete(application.initialize())
    ptb_loop.run_until_complete(application.start())
    ptb_loop.run_forever()

# Start PTB in a separate thread
threading.Thread(target=run_ptb, daemon=True).start()

@app.post("/webhook")
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)

    # Schedule update processing on PTB loop
    asyncio.run_coroutine_threadsafe(application.process_update(update), ptb_loop)

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("Listening on port:", port)
    app.run(host="0.0.0.0", port=port)
