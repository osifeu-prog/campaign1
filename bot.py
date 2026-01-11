
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers.start import start
from handlers.register import register
from handlers.expert import expert
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

tg_app = Application.builder().token(TOKEN).build()

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("register", register))
tg_app.add_handler(CommandHandler("expert", expert))
