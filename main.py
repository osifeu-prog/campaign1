import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application

from handlers.start import start_handler
from handlers.help_all import all_handler
from handlers.images import image_handler, resize_handler

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI()

tg_app = Application.builder().token(TOKEN).build()

tg_app.add_handler(start_handler)
tg_app.add_handler(all_handler)
tg_app.add_handler(image_handler)
tg_app.add_handler(resize_handler)

@app.on_event("startup")
async def startup():
    await tg_app.bot.set_webhook(WEBHOOK_URL)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}
