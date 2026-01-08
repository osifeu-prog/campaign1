import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import uvicorn
from bot import bot_handlers
import sheets_service


# ------------------ ENV VALIDATION ------------------

def validate_env():
    required_vars = {
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "GOOGLE_CREDENTIALS_JSON": os.getenv("GOOGLE_CREDENTIALS_JSON"),
        "GOOGLE_SHEETS_SPREADSHEET_ID": os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"),
    }

    optional_vars = {
        "LOG_GROUP_ID": os.getenv("LOG_GROUP_ID"),
        "ALL_MEMBERS_GROUP_ID": os.getenv("ALL_MEMBERS_GROUP_ID"),
        "ACTIVISTS_GROUP_ID": os.getenv("ACTIVISTS_GROUP_ID"),
        "EXPERTS_GROUP_ID": os.getenv("EXPERTS_GROUP_ID"),
        "SUPPORT_GROUP_ID": os.getenv("SUPPORT_GROUP_ID"),
        "ADMIN_IDS": os.getenv("ADMIN_IDS"),
    }

    print("=== ENVIRONMENT VALIDATION START ===")

    for key, value in required_vars.items():
        if not value:
            print(f"[WARNING] Missing REQUIRED variable: {key}")
        else:
            print(f"[OK] {key} loaded")

    for key, value in optional_vars.items():
        if not value:
            print(f"[INFO] Optional variable missing: {key}")
        else:
            print(f"[OK] {key} loaded")

    print("=== ENVIRONMENT VALIDATION END ===")


# ------------------ BOT SETUP ------------------

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = FastAPI()

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Conversation handler
application.add_handler(bot_handlers.get_conversation_handler())

# Utility commands
application.add_handler(CommandHandler("myid", bot_handlers.my_id))
application.add_handler(CommandHandler("groupid", bot_handlers.group_id))
application.add_handler(CommandHandler("ALL", bot_handlers.all_commands))

# Positions commands
application.add_handler(CommandHandler("positions", bot_handlers.list_positions))
application.add_handler(CommandHandler("position", bot_handlers.position_details))
application.add_handler(CommandHandler("assign", bot_handlers.assign_position))

# Support command
application.add_handler(CommandHandler("support", bot_handlers.support))

# Admin callbacks
application.add_handler(
    CallbackQueryHandler(bot_handlers.expert_admin_callback, pattern="^expert_")
)


# ------------------ STARTUP ------------------

@app.on_event("startup")
async def startup_event():
    validate_env()

    await application.initialize()
    await application.start()
    print("Bot initialized and started")

    try:
        sheets_service.init_positions()
        print("Positions sheet initialized/verified")
    except Exception as e:
        print("Error initializing Positions sheet:", e)


# ------------------ WEBHOOK ------------------

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}


# ------------------ RUN LOCAL ------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
