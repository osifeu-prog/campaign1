import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import uvicorn
import bot_handlers
import sheets_service

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = FastAPI()

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Conversation handler
application.add_handler(bot_handlers.get_conversation_handler())

# פקודות מערכת
application.add_handler(CommandHandler("groupid", bot_handlers.group_id))
application.add_handler(CommandHandler("positions", bot_handlers.list_positions))
application.add_handler(CommandHandler("position", bot_handlers.position_details))
application.add_handler(CommandHandler("assign", bot_handlers.assign_position))

# כפתורי אדמין למומחים
application.add_handler(
    CallbackQueryHandler(bot_handlers.expert_admin_callback, pattern="^expert_")
)


@app.on_event("startup")
async def startup_event():
    await application.initialize()
    await application.start()
    print("Bot initialized and started")

    try:
        sheets_service.init_positions()
        print("Positions sheet initialized/verified")
    except Exception as e:
        print("Error initializing Positions sheet:", e)


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
