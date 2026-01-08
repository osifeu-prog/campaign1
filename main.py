import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
import uvicorn
import bot_handlers

# ENV variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")
LOG_GROUP_ID = os.getenv("LOG_GROUP_ID")
EXPERTS_GROUP_ID = os.getenv("EXPERTS_GROUP_ID")
SUPPORTERS_GROUP_ID = os.getenv("SUPPORTERS_GROUP_ID")

app = FastAPI()

# Create PTB application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Register conversation handler
application.add_handler(bot_handlers.get_conversation_handler())


@app.on_event("startup")
async def startup_event():
    await application.initialize()
    await application.start()
    print("Bot initialized and started")


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
