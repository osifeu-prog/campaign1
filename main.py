
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import CommandHandler

from bot.app import build_application
from bot.handlers.common import start, help_cmd
from bot.handlers.user import register, status
from bot.handlers.expert import expert
from bot.handlers.admin import admin_menu
from config.settings import WEBHOOK_URL, PORT
from services.logger import logger

app = FastAPI()
tg_app = build_application()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("help", help_cmd))
tg_app.add_handler(CommandHandler("register", register))
tg_app.add_handler(CommandHandler("status", status))
tg_app.add_handler(CommandHandler("expert", expert))
tg_app.add_handler(CommandHandler("admin", admin_menu))


@app.on_event("startup")
async def on_startup():
    logger.info("Starting Telegram bot (webhook mode)")
    await tg_app.initialize()
    await tg_app.bot.set_webhook(WEBHOOK_URL)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}


if name == "main":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
