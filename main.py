import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters as tg_filters,
)
import uvicorn

from bot import bot_handlers
import sheets_service


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


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Cannot start bot.")

app = FastAPI()

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Conversation handler
application.add_handler(bot_handlers.get_conversation_handler())

# Regular commands
application.add_handler(CommandHandler("myid", bot_handlers.my_id))
application.add_handler(CommandHandler("groupid", bot_handlers.group_id))

# Menus & help
application.add_handler(CommandHandler("menu", bot_handlers.menu_command))
application.add_handler(CommandHandler("help", bot_handlers.menu_command))
application.add_handler(CommandHandler("ALL", bot_handlers.all_commands))
application.add_handler(CommandHandler("all", bot_handlers.all_commands))

# Positions & admin tools
application.add_handler(CommandHandler("positions", bot_handlers.list_positions))
application.add_handler(CommandHandler("position", bot_handlers.position_details))
application.add_handler(CommandHandler("assign", bot_handlers.assign_position))
application.add_handler(CommandHandler("reset_position", bot_handlers.reset_position_cmd))
application.add_handler(CommandHandler("reset_all_positions", bot_handlers.reset_all_positions_cmd))

# Support
application.add_handler(CommandHandler("support", bot_handlers.support))

# Expert group
application.add_handler(CommandHandler("set_expert_group", bot_handlers.set_expert_group))

# Admin menu
application.add_handler(CommandHandler("admin_menu", bot_handlers.admin_menu))

# Expert admin callbacks (אישור/דחייה)
application.add_handler(
    CallbackQueryHandler(bot_handlers.expert_admin_callback, pattern="^expert_(approve|reject):")
)

# Unknown commands handler – מסונן כדי לא לבלוע פקודות מוכרות
KNOWN_COMMANDS_PATTERN = (
    r"^/(start|menu|help|ALL|all|myid|groupid|"
    r"positions|position|assign|support|set_expert_group|"
    r"admin_menu|reset_position|reset_all_positions)"
    r"(?:@[\w_]+)?\b"
)

application.add_handler(
    MessageHandler(
        tg_filters.COMMAND & ~tg_filters.Regex(KNOWN_COMMANDS_PATTERN),
        bot_handlers.unknown_command
    ),
    group=1,
)


@app.on_event("startup")
async def startup_event():
    validate_env()

    await application.initialize()
    await application.start()
    print("Bot initialized and started")

    try:
        sheets_service.init_positions()
        print("Positions sheet initialized or verified")
    except Exception as e:
        print("Error initializing Positions sheet:", e)


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "ignored"}

    update = Update.de_json(data, application.bot)

    try:
        await application.process_update(update)
    except Exception as e:
        print("Error processing update:", e)

    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
