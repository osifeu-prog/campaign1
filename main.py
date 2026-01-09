# ===============================
# main.py – נקודת כניסה לבוט
# ===============================

import os

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# --- ייבוא מודולים מהבוט ---
from bot import bot_handlers
from bot.admin_handlers import (
    list_positions,
    position_details,
    assign_position_cmd,
    reset_position_cmd,
    reset_all_positions_cmd,
    fix_sheets,
    validate_sheets,
    sheet_info,
    clear_expert_duplicates_cmd,
    clear_user_duplicates_cmd,
    find_user,
    find_expert,
    find_position,
    list_approved_experts,
    list_rejected_experts,
    list_supporters,
    admin_menu,
    expert_admin_callback,
)

# --- שירותי שיטס ---
from services import sheets_service


# ===============================
# הגדרות בסיס
# ===============================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # למשל: https://campaign1-production.up.railway.app/webhook

app = FastAPI()

application = (
    ApplicationBuilder()
    .token(TOKEN)
    .build()
)


# ===============================
# בדיקת ENV
# ===============================

def validate_env():
    if not TOKEN:
        raise Exception("Missing TELEGRAM_BOT_TOKEN")
    if not sheets_service.SPREADSHEET_ID:
        raise Exception("Missing GOOGLE_SHEETS_SPREADSHEET_ID")


# ===============================
# Startup
# ===============================

@app.on_event("startup")
async def startup_event():
    validate_env()

    print("Validating Google Sheets structure...")
    try:
        sheets_service.validate_all_sheets()
    except Exception as e:
        print("❌ Sheets validation failed:", e)
        raise

    # ConversationHandler הראשי
    conv_handler = bot_handlers.get_conversation_handler()
    application.add_handler(conv_handler)

    # --- סדר נכון של CallbackQueryHandlers ---

    # 1) קודם callbacks של אישור/דחיית מומחים
    application.add_handler(CallbackQueryHandler(
        expert_admin_callback,
        pattern=r"^expert_(approve|reject):"
    ))

    # 2) אחר כך כל שאר ה־callbacks של התפריטים
    application.add_handler(CallbackQueryHandler(
        bot_handlers.handle_menu_callback
    ))

    # --- פקודות כלליות ---
    application.add_handler(CommandHandler("menu", bot_handlers.menu_command))
    application.add_handler(CommandHandler("help", bot_handlers.all_commands))
    application.add_handler(CommandHandler("myid", bot_handlers.my_id))
    application.add_handler(CommandHandler("groupid", bot_handlers.group_id))

    # --- פקודות אדמין – מקומות ---
    application.add_handler(CommandHandler("positions", list_positions))
    application.add_handler(CommandHandler("position", position_details))
    application.add_handler(CommandHandler("assign", assign_position_cmd))
    application.add_handler(CommandHandler("reset_position", reset_position_cmd))
    application.add_handler(CommandHandler("reset_all_positions", reset_all_positions_cmd))

    # --- פקודות אדמין – שיטס ---
    application.add_handler(CommandHandler("fix_sheets", fix_sheets))
    application.add_handler(CommandHandler("validate_sheets", validate_sheets))
    application.add_handler(CommandHandler("sheet_info", sheet_info))
    application.add_handler(CommandHandler("clear_expert_duplicates", clear_expert_duplicates_cmd))
    application.add_handler(CommandHandler("clear_user_duplicates", clear_user_duplicates_cmd))

    # --- פקודות אדמין – חיפוש ורשימות ---
    application.add_handler(CommandHandler("find_user", find_user))
    application.add_handler(CommandHandler("find_expert", find_expert))
    application.add_handler(CommandHandler("find_position", find_position))
    application.add_handler(CommandHandler("list_approved_experts", list_approved_experts))
    application.add_handler(CommandHandler("list_rejected_experts", list_rejected_experts))
    application.add_handler(CommandHandler("list_supporters", list_supporters))
    application.add_handler(CommandHandler("admin_menu", admin_menu))

    # --- פקודות לא מוכרות ---
    application.add_handler(MessageHandler(filters.COMMAND, bot_handlers.unknown_command))

    await application.initialize()
    await application.start()
    print("Bot initialized and started")


# ===============================
# Webhook endpoint
# ===============================

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    נקודת קצה לקבלת עדכונים מהטלגרם
    """
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
