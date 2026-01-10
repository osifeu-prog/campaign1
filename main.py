# main.py
# ==========================================
# Campaign1 Bot – Full Production Entry Point
# FastAPI + Telegram Webhook + All Handlers
# ==========================================

import os
import traceback

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Core
from bot.core.monitoring import monitoring

# Handlers
from bot.handlers import bot_handlers
from bot.handlers.admin_handlers import (
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
    broadcast_supporters,
    broadcast_experts,
    dashboard_command,
    hourly_stats_command,
    export_metrics_command,
    handle_experts_pagination,
    handle_supporters_pagination,
)
from bot.handlers.donation_handlers import (
    handle_donation_callback,
    handle_copy_wallet_callback,
    handle_ton_info_callback,
)
from bot.handlers.image_handlers import (
    handle_photo_message,
    handle_animation_message,
)

# Constants
from utils.constants import (
    TELEGRAM_BOT_TOKEN,
    WEBHOOK_URL,
    CALLBACK_DONATE,
    CALLBACK_COPY_WALLET,
    CALLBACK_TON_INFO,
    CALLBACK_START_SLIDE,
    CALLBACK_START_SOCI,
    CALLBACK_START_FINISH,
)

# Sheets
from services.sheets_service import sheets_service


# ==========================================
# FastAPI App
# ==========================================

app = FastAPI(title="Campaign1 Bot API", version="2.0.0")

application = (
    ApplicationBuilder()
    .token(TELEGRAM_BOT_TOKEN)
    .concurrent_updates(True)
    .build()
)


# ==========================================
# Startup
# ==========================================

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting Campaign1 Bot...")

    # Validate Google Sheets
    try:
        sheets_service.smart_validate_sheets()
        print("✔ Google Sheets validated")
    except Exception as e:
        print("⚠ Sheets validation failed:", e)

    # Register ConversationHandler
    conv = bot_handlers.get_conversation_handler()
    application.add_handler(conv)

    # Callback handlers
    application.add_handler(CallbackQueryHandler(expert_admin_callback, pattern=r"^expert_"))
    application.add_handler(CallbackQueryHandler(handle_donation_callback, pattern=CALLBACK_DONATE))
    application.add_handler(CallbackQueryHandler(handle_copy_wallet_callback, pattern=CALLBACK_COPY_WALLET))
    application.add_handler(CallbackQueryHandler(handle_ton_info_callback, pattern=CALLBACK_TON_INFO))
    application.add_handler(CallbackQueryHandler(handle_experts_pagination, pattern=r"^experts_page"))
    application.add_handler(CallbackQueryHandler(handle_supporters_pagination, pattern=r"^supporters_page"))
    application.add_handler(CallbackQueryHandler(bot_handlers.handle_start_callback_entry,
                                                pattern=rf"^{CALLBACK_START_SLIDE}:|^{CALLBACK_START_SOCI}$|^{CALLBACK_START_FINISH}$"))
    application.add_handler(CallbackQueryHandler(bot_handlers.handle_menu_callback))

    # Commands
    application.add_handler(CommandHandler("start", bot_handlers.start))
    application.add_handler(CommandHandler("menu", bot_handlers.menu_command))
    application.add_handler(CommandHandler("help", bot_handlers.all_commands))
    application.add_handler(CommandHandler("myid", bot_handlers.my_id))
    application.add_handler(CommandHandler("groupid", bot_handlers.group_id))

    # Admin commands
    application.add_handler(CommandHandler("positions", list_positions))
    application.add_handler(CommandHandler("position", position_details))
    application.add_handler(CommandHandler("assign", assign_position_cmd))
    application.add_handler(CommandHandler("reset_position", reset_position_cmd))
    application.add_handler(CommandHandler("reset_all_positions", reset_all_positions_cmd))
    application.add_handler(CommandHandler("fix_sheets", fix_sheets))
    application.add_handler(CommandHandler("validate_sheets", validate_sheets))
    application.add_handler(CommandHandler("sheet_info", sheet_info))
    application.add_handler(CommandHandler("clear_user_duplicates", clear_user_duplicates_cmd))
    application.add_handler(CommandHandler("clear_expert_duplicates", clear_expert_duplicates_cmd))
    application.add_handler(CommandHandler("find_user", find_user))
    application.add_handler(CommandHandler("find_expert", find_expert))
    application.add_handler(CommandHandler("find_position", find_position))
    application.add_handler(CommandHandler("list_approved_experts", list_approved_experts))
    application.add_handler(CommandHandler("list_rejected_experts", list_rejected_experts))
    application.add_handler(CommandHandler("list_supporters", list_supporters))
    application.add_handler(CommandHandler("admin_menu", admin_menu))
    application.add_handler(CommandHandler("broadcast_supporters", broadcast_supporters))
    application.add_handler(CommandHandler("broadcast_experts", broadcast_experts))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("hourly_stats", hourly_stats_command))
    application.add_handler(CommandHandler("export_metrics", export_metrics_command))

    # Media handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    application.add_handler(MessageHandler(filters.ANIMATION | filters.Document.IMAGE, handle_animation_message))

    # Unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, bot_handlers.unknown_command))

    # Start bot
    await application.initialize()
    await application.start()

    # Webhook
    final_url = WEBHOOK_URL.rstrip("/") + "/webhook"
    await application.bot.set_webhook(final_url, drop_pending_updates=True)
    print(f"✔ Webhook set: {final_url}")

    print("🤖 Campaign1 Bot is running!")


# ==========================================
# Webhook Endpoint
# ==========================================

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)

        if update:
            if update.message and update.message.from_user:
                monitoring.track_message(update.message.from_user.id)
            await application.process_update(update)

        return {"ok": True}

    except Exception as e:
        print("❌ Error processing update:", e)
        traceback.print_exc()
        return {"ok": False}


# ==========================================
# Health Check
# ==========================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "bot": application.bot.username if application.bot else None,
        "messages_today": monitoring.metrics.messages_today,
    }
