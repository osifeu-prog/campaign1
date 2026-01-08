from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler
import os
import asyncio
import bot_handlers

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = Flask(__name__)

# Create application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Register handlers
application.add_handler(CommandHandler("start", bot_handlers.start))

# Initialize PTB once at startup
async def init_bot():
    await application.initialize()
    await application.start()

asyncio.get_event_loop().run_until_complete(init_bot())

@app.post("/webhook")
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)

    # Process update asynchronously
    asyncio.get_event_loop().run_until_complete(application.process_update(update))

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("Listening on port:", port)
    app.run(host="0.0.0.0", port=port)
