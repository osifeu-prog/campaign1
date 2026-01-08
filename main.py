import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
import uvicorn
import bot_handlers

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Optional environment variables for later use (admin, log groups, etc.)
ADMIN_IDS = os.getenv("ADMIN_IDS", "")  # e.g. "123456789,987654321"
LOG_GROUP_ID = os.getenv("LOG_GROUP_ID")  # e.g. "-1001234567890"
EXPERTS_GROUP_ID = os.getenv("EXPERTS_GROUP_ID")
SUPPORTERS_GROUP_ID = os.getenv("SUPPORTERS_GROUP_ID")

app = FastAPI()

# Create PTB application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Register conversation handler from bot_handlers
application.add_handler(bot_handlers.get_conversation_handler())


@app.on_event("startup")
async def startup_event():
    """Initialize the Telegram bot when the FastAPI app starts."""
    await application.initialize()
    await application.start()
    print("Bot initialized and started")


@app.post("/webhook")
async def webhook(request: Request):
    """Telegram webhook endpoint."""
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
