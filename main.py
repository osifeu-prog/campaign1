# main.py  נקודת כניסה משודרגת עם בדיקות והרשאות Google מפורטות

import hotfixes
import os
import sys
import traceback
import json
import time

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

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
    broadcast_supporters,
    broadcast_experts,
    dashboard_command,
    hourly_stats_command,
    export_metrics_command,
    handle_experts_pagination,
    handle_supporters_pagination,
    backup_sheets_cmd,
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

# expert admin actions באים מהמומחים, לא מהאדמין
from bot.handlers.expert_handlers import expert_admin_callback

from bot.flows import start_flow

# IMPORTANT: import the sheets_service instance directly from the module
from services.sheets_service import sheets_service

from utils.constants import (
    CALLBACK_START_SLIDE,
    CALLBACK_START_SOCI,
    CALLBACK_START_FINISH,
    CALLBACK_DONATE,
    CALLBACK_COPY_WALLET,
    CALLBACK_TON_INFO,
    GOOGLE_SHEETS_SPREADSHEET_ID,
    GOOGLE_CREDENTIALS_JSON,
)
from bot.core.monitoring import monitoring

# ===============================
# ENV
# ===============================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

if not TOKEN:
    print("❌ ERROR: Missing TELEGRAM_BOT_TOKEN", file=sys.stderr)
    raise SystemExit(1)

if not WEBHOOK_URL:
    print("❌ ERROR: Missing WEBHOOK_URL", file=sys.stderr)
    raise SystemExit(1)

# Normalize WEBHOOK_URL: ensure it does not end with a trailing slash
WEBHOOK_URL = WEBHOOK_URL.rstrip("/")

# If the provided WEBHOOK_URL already contains '/webhook' at the end, use it as-is.
# Otherwise append '/webhook' so the final webhook path is consistent with FastAPI route.
if WEBHOOK_URL.endswith("/webhook"):
    final_webhook_url = WEBHOOK_URL
else:
    final_webhook_url = f"{WEBHOOK_URL}/webhook"

# ===============================
# FastAPI + Telegram Application
# ===============================

app = FastAPI(title="Campaign1 Bot API", version="2.0.0")

application = (
    ApplicationBuilder()
    .token(TOKEN)
    .concurrent_updates(True)
    .build()
)

# ===============================
# Global error handler
# ===============================
async def _global_error_handler(update, context):
    """
    Catches unhandled exceptions from handlers, logs traceback and notifies user gracefully.
    """
    try:
        import traceback as _tb
        print("❌ Unhandled exception in update handler:", file=sys.stderr)
        try:
            _tb.print_exception(type(context.error), context.error, context.error.__traceback__)
        except Exception:
            print("Error printing exception details", file=sys.stderr)

        # Try to notify the user in a friendly way (best-effort)
        try:
            chat_id = None
            if update:
                if getattr(update, "effective_chat", None):
                    chat_id = update.effective_chat.id
                elif getattr(update, "message", None) and update.message.chat:
                    chat_id = update.message.chat.id
            if chat_id:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="אירעה שגיאה פנימית בעיבוד הבקשה. אנא נסה שנית בעוד רגע."
                )
        except Exception:
            pass
    except Exception as e:
        print("❌ Error in global error handler:", e, file=sys.stderr)

# ===============================
# בדיקת ENV + בדיקות הרשאות Google
# ===============================

def _log_google_auth_issue(exc: Exception):
    msg = str(exc) or ""
    if "401" in msg or "unauthorized" in msg.lower() or "invalid" in msg.lower():
        print("❌ Google Auth Error detected: 401 Unauthorized or invalid credentials", file=sys.stderr)
        print(f"   Details: {msg}", file=sys.stderr)
        print("   Suggestion: Verify GOOGLE_CREDENTIALS_JSON and that the Service Account has access to the spreadsheet.", file=sys.stderr)
    elif "403" in msg or "forbidden" in msg.lower() or "access" in msg.lower():
        print("❌ Google Auth Error detected: 403 Forbidden or insufficient permissions", file=sys.stderr)
        print(f"   Details: {msg}", file=sys.stderr)
        print("   Suggestion: Ensure the Service Account is granted Editor access to the spreadsheet and Drive API is enabled.", file=sys.stderr)
    else:
        print("❌ Google API error during client initialization:", file=sys.stderr)
        print(f"   {msg}", file=sys.stderr)

def validate_env():
    """
    Validate required environment variables and attempt to initialize Google Sheets client.
    Raises Exception on fatal missing configuration or unrecoverable auth errors.
    """
    # Basic required env vars check
    required_vars = {
        "TELEGRAM_BOT_TOKEN": TOKEN,
        "WEBHOOK_URL": WEBHOOK_URL,
        "GOOGLE_SHEETS_SPREADSHEET_ID": GOOGLE_SHEETS_SPREADSHEET_ID,
        "GOOGLE_CREDENTIALS_JSON": GOOGLE_CREDENTIALS_JSON,
    }
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        raise Exception(f"Missing required ENV variables: {', '.join(missing)}")

    # If sheets_service already marked degraded, propagate flag
    try:
        if getattr(sheets_service, "_degraded", False):
            application.bot_data['sheets_degraded'] = True
            print('⚠ Sheets degraded mode detected at startup')
    except Exception:
        pass

    # Try to initialize or validate the sheets client
    try:
        if hasattr(sheets_service, "_init_client"):
            sheets_service._init_client()
        elif hasattr(sheets_service, "smart_validate_sheets"):
            sheets_service.smart_validate_sheets()
        else:
            print("⚠ No sheets init method found; continuing without explicit validation", file=sys.stderr)

        # Quick verification: try to access spreadsheet properties if available
        sp = getattr(sheets_service, "_spreadsheet", None)
        if sp and getattr(sp, "_properties", None):
            title = sp._properties.get("title", "<unknown>")
            print(f"✔ Google Sheets access verified for spreadsheet: {title}")
        else:
            try:
                if sp is not None:
                    _ = sp.worksheets()
                    print("✔ Google Sheets access verified (worksheets listed).")
            except Exception as inner_exc:
                _log_google_auth_issue(inner_exc)
                raise
    except Exception as e:
        _log_google_auth_issue(e)
        raise

# ===============================
# /leaderboard command (מקומית כאן)
# ===============================

async def leaderboard_command(update, context):
    user = update.effective_user
    leaders = sheets_service.get_experts_leaderboard()
    if not leaders:
        await update.message.reply_text("אין מומחים בדירוג כרגע.")
        return
    text = "🏆 טבלת מובילים - מומחים לפי מספר תומכים:\n\n"
    for idx, row in enumerate(leaders, start=1):
        name = row.get("expert_full_name", "—")
        pos = row.get("expert_position", "—")
        supporters = row.get("supporters_count", 0)
        text += f"{idx}. {name} — מקום {pos} — תומכים: {supporters}\n"
    await update.message.reply_text(text)

# ===============================
# Startup  טעינת הבוט
# ===============================

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting bot initialization...")

    # Validate environment and Google Sheets access (best-effort)
    try:
        validate_env()
        print("✔ ENV validation passed")
    except Exception as e:
        print(f"❌ ENV validation failed: {e}", file=sys.stderr)
        traceback.print_exc()
        # Mark degraded mode but continue startup
        try:
            application.bot_data['sheets_degraded'] = True
            print("⚠ Continuing startup in degraded mode (Sheets unavailable).")
        except Exception:
            pass

    print("🔍 Running Smart Validation on Google Sheets (best-effort)...")
    try:
        if hasattr(sheets_service, "smart_validate_sheets"):
            sheets_service.smart_validate_sheets()
            print("✔ Sheets validated successfully")
        else:
            print("⚠ smart_validate_sheets not available; skipping detailed validation")
    except Exception as e:
        print("❌ CRITICAL: Smart Validation failed!", file=sys.stderr)
        traceback.print_exc()
        print("⚠️ Continuing startup WITHOUT sheet validation. Be aware some features may fail at runtime.", file=sys.stderr)
        try:
            application.bot_data['sheets_degraded'] = True
        except Exception:
            pass

    print("🔧 Initializing bot handlers...")

    # Register global error handler
    try:
        application.add_error_handler(_global_error_handler)
        print("✔ Global error handler registered")
    except Exception as e:
        print("⚠ Failed to register global error handler:", e, file=sys.stderr)

    # ConversationHandler הראשי (start + flows)
    try:
        conv_handler = bot_handlers.get_conversation_handler()
        if conv_handler:
            application.add_handler(conv_handler)
            print("✔ ConversationHandler registered")
    except Exception as e:
        print("⚠ Failed to register ConversationHandler:", e, file=sys.stderr)

    # --- Callback handlers בסדר נכון ---
    try:
        application.add_handler(CallbackQueryHandler(
            expert_admin_callback,
            pattern=r"^expert_(approve|reject):"
        ))

        application.add_handler(CallbackQueryHandler(
            handle_donation_callback,
            pattern=rf"^{CALLBACK_DONATE}$"
        ))
        application.add_handler(CallbackQueryHandler(handle_copy_wallet_callback, pattern=rf"^{CALLBACK_COPY_WALLET}$"))
        application.add_handler(CallbackQueryHandler(handle_ton_info_callback, pattern=rf"^{CALLBACK_TON_INFO}$"))

        application.add_handler(CallbackQueryHandler(
            handle_experts_pagination,
            pattern=r"^experts_page:"
        ))
        application.add_handler(CallbackQueryHandler(
            handle_supporters_pagination,
            pattern=r"^supporters_page:"
        ))

        # קרוסלה של /start – עכשיו ישירות ל־start_flow.handle_start_callback
        application.add_handler(CallbackQueryHandler(
            start_flow.handle_start_callback,
            pattern=rf"^{CALLBACK_START_SLIDE}:|^{CALLBACK_START_SOCI}$|^{CALLBACK_START_FINISH}$"
        ))

        # תפריט – route דרך menu_flow בתוך bot_handlers
        application.add_handler(CallbackQueryHandler(
            bot_handlers.handle_menu_callback
        ))
        print("✔ Callback handlers registered")
    except Exception as e:
        print("⚠ Failed to register some callback handlers:", e, file=sys.stderr)
        traceback.print_exc()

    # --- פקודות כלליות ---
    try:
        application.add_handler(CommandHandler("start", bot_handlers.start))
        application.add_handler(CommandHandler("menu", bot_handlers.menu_command))
        application.add_handler(CommandHandler("help", bot_handlers.all_commands))
        application.add_handler(CommandHandler("myid", bot_handlers.my_id))
        application.add_handler(CommandHandler("groupid", bot_handlers.group_id))
        application.add_handler(CommandHandler("leaderboard", leaderboard_command))
        print("✔ General command handlers registered")
    except Exception as e:
        print("⚠ Failed to register general commands:", e, file=sys.stderr)

    # --- פקודות אדמין  מקומות ---
    try:
        application.add_handler(CommandHandler("positions", list_positions))
        application.add_handler(CommandHandler("position", position_details))
        application.add_handler(CommandHandler("assign", assign_position_cmd))
        application.add_handler(CommandHandler("reset_position", reset_position_cmd))
        application.add_handler(CommandHandler("reset_all_positions", reset_all_positions_cmd))
        print("✔ Admin position commands registered")
    except Exception as e:
        print("⚠ Failed to register admin position commands:", e, file=sys.stderr)

    # --- פקודות אדמין  שיטס ---
    try:
        application.add_handler(CommandHandler("fix_sheets", fix_sheets))
        application.add_handler(CommandHandler("validate_sheets", validate_sheets))
        application.add_handler(CommandHandler("sheet_info", sheet_info))
        application.add_handler(CommandHandler("clear_expert_duplicates", clear_expert_duplicates_cmd))
        application.add_handler(CommandHandler("clear_user_duplicates", clear_user_duplicates_cmd))
        application.add_handler(CommandHandler("backup_sheets", backup_sheets_cmd))
        print("✔ Admin sheets commands registered")
    except Exception as e:
        print("⚠ Failed to register admin sheets commands:", e, file=sys.stderr)

    # --- פקודות אדמין  חיפוש ורשימות ---
    try:
        application.add_handler(CommandHandler("find_user", find_user))
        application.add_handler(CommandHandler("find_expert", find_expert))
        application.add_handler(CommandHandler("find_position", find_position))
        application.add_handler(CommandHandler("list_approved_experts", list_approved_experts))
        application.add_handler(CommandHandler("list_rejected_experts", list_rejected_experts))
        application.add_handler(CommandHandler("list_supporters", list_supporters))
        application.add_handler(CommandHandler("admin_menu", admin_menu))
        print("✔ Admin search/list commands registered")
    except Exception as e:
        print("⚠ Failed to register admin search/list commands:", e, file=sys.stderr)

    # --- פקודות אדמין  שידור ---
    try:
        application.add_handler(CommandHandler("broadcast_supporters", broadcast_supporters))
        application.add_handler(CommandHandler("broadcast_experts", broadcast_experts))
        print("✔ Broadcast commands registered")
    except Exception as e:
        print("⚠ Failed to register broadcast commands:", e, file=sys.stderr)

    # --- פקודות אדמין  Monitoring ---
    try:
        application.add_handler(CommandHandler("dashboard", dashboard_command))
        application.add_handler(CommandHandler("hourly_stats", hourly_stats_command))
        application.add_handler(CommandHandler("export_metrics", export_metrics_command))
        print("✔ Monitoring commands registered")
    except Exception as e:
        print("⚠ Failed to register monitoring commands:", e, file=sys.stderr)

    # --- פקודות לא מוכרות (fallback כללי) ---
    try:
        application.add_handler(MessageHandler(filters.COMMAND, bot_handlers.unknown_command))
    except Exception as e:
        print("⚠ Failed to register unknown command handler:", e, file=sys.stderr)

    # --- image handlers (photos / animations) ---
    try:
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
        application.add_handler(MessageHandler(filters.ANIMATION | filters.Document.IMAGE, handle_animation_message))
        print("✔ Image handlers registered")
    except Exception as e:
        print("⚠ Failed to register image handlers:", e, file=sys.stderr)

    # --- הפעלת הבוט ---
    try:
        await application.initialize()
        await application.start()
    except Exception as e:
        print(f"❌ Failed to initialize/start application: {e}", file=sys.stderr)
        traceback.print_exc()
        raise

    # ✅ הגדרת Webhook
    try:
        await application.bot.set_webhook(
            url=final_webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        print(f"✔ Webhook set successfully: {final_webhook_url}")
    except Exception as e:
        print(f"❌ Failed to set webhook: {e}", file=sys.stderr)
        traceback.print_exc()
        raise

    # עדכון מטריקות ראשוני
    try:
        monitoring.update_metrics_from_sheets()
    except Exception as e:
        print("⚠ Failed to update monitoring metrics from sheets:", file=sys.stderr)
        traceback.print_exc()

    # הגדרת Cleanup Job (אם JobQueue זמין)
    try:
        from datetime import time as _time
        if getattr(application, "job_queue", None) is not None:
            application.job_queue.run_daily(
                cleanup_monitoring_job,
                time=_time(hour=0, minute=5)
            )
            print("✔ Cleanup job scheduled with JobQueue")
        else:
            print("⚠ JobQueue not available. Skipping scheduled cleanup job.", file=sys.stderr)
    except Exception as e:
        print(f"⚠ Failed to schedule cleanup job: {e}", file=sys.stderr)

    print("🤖 Bot initialized and running!")

# פונקציית ניקוי מתוזמנת
async def cleanup_monitoring_job(context):
    """
    ניקוי נתונים ישנים - רץ פעם ביום
    """
    try:
        monitoring.cleanup_old_data(days_to_keep=7)
        print("✔ Monitoring data cleanup completed")
    except Exception as e:
        print("⚠ Cleanup job failed:", e, file=sys.stderr)

@app.on_event("shutdown")
async def shutdown_event():
    """
    כיבוי נקי של הבוט
    """
    print("🛑 Shutting down bot...")
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
        await application.stop()
        await application.shutdown()
        print("✔ Bot shutdown complete")
    except Exception as e:
        print(f"⚠️ Error during shutdown: {e}", file=sys.stderr)

# ===============================
# Webhook endpoint
# ===============================

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    נקודת קצה לקבלת עדכונים מ‑Telegram.
    מוסיף לוגינג של ה‑payload כדי לאבחן בעיות חיבור.
    """
    try:
        raw = await request.body()
        text = raw.decode("utf-8") if raw else ""
        print("🔔 Incoming webhook payload (truncated 200 chars):")
        print(text[:200])

        data = await request.json()
        update = Update.de_json(data, application.bot)

        if update:
            if update.message and update.message.from_user:
                monitoring.track_message(
                    update.message.from_user.id,
                    "message"
                )
                if update.message.text and update.message.text.startswith("/"):
                    cmd = update.message.text.split()[0][1:]
                    monitoring.track_command(cmd)

            await application.process_update(update)
            return {"ok": True}
        else:
            return {"ok": False, "error": "Invalid update"}

    except Exception as e:
        print("❌ Error processing update:", e, file=sys.stderr)
        traceback.print_exc()
        try:
            monitoring.track_error("webhook_processing", str(e))
        except Exception:
            pass
        return {"ok": False, "error": str(e)}

@app.get("/health")
async def health_check():
    """
    בדיקת בריאות לשימוש Railway
    """
    bot_username = None
    try:
        bot_username = application.bot.username if application and application.bot else None
    except Exception:
        bot_username = None

    return {
        "status": "healthy",
        "bot_username": bot_username,
        "metrics": {
            "total_users": monitoring.metrics.total_users,
            "messages_today": monitoring.metrics.messages_today,
        }
    }

@app.get("/")
async def root():
    """
    עמוד בית
    """
    bot_username = None
    try:
        bot_username = application.bot.username if application and application.bot else None
    except Exception:
        bot_username = None

    return {
        "service": "Campaign1 Bot",
        "version": "2.0.0",
        "status": "running",
        "bot": bot_username,
    }

# Prevent duplicate ConversationHandler registration (utility)
def _conversation_handler_registered(app_obj, handler_type_name="ConversationHandler"):
    try:
        for group_handlers in getattr(app_obj, "handlers", {}).values():
            for h in group_handlers:
                if type(h).__name__ == handler_type_name:
                    return True
    except Exception:
        pass
    return False

# Defensive registration at module import time (if needed)
try:
    if not _conversation_handler_registered(application):
        conv_handler = bot_handlers.get_conversation_handler()
        if conv_handler:
            application.add_handler(conv_handler)
            print("✔ ConversationHandler registered at import time")
except Exception:
    pass
