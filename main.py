import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler
import uvicorn
import bot_handlers

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = FastAPI()

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Conversation handler
application.add_handler(bot_handlers.get_conversation_handler())

# Group ID command
application.add_handler(CommandHandler("groupid", bot_handlers.group_id))


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
