import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler
import uvicorn
import bot_handlers

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Create FastAPI app
app = FastAPI()

# Create PTB application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Register handlers
application.add_handler(CommandHandler("start", bot_handlers.start))

# Initialize PTB once at startup
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
