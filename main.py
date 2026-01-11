# main.py – נקודת כניסה משודרגת עם בדיקות והרשאות Google מפורטות
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
    expert_admin_callback,
    broadcast_supporters,
    broadcast_experts,
    dashboard_command,
    hourly_stats_command,
    export_metrics_command,
    handle_experts_pagination,
    handle_supporters_pagination,
    leaderboard_command,
    backup_sheets_cmd,
)
from bot.handlers.donation_handlers import (
    handle_donation_callback,
    check_donation_status,
    handle_copy_wallet_callback,
    handle_ton_info_callback,
)

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

# image handlers (registered later)
from bot.handlers import image_handlers

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
# בדיקת ENV + בדיקות הרשאות Google
# ===============================

def _log_google_auth_issue(exc: Exception):
    """
    ניתוח שגיאות כדי לזהות 401/403 ולהדפיס הודעות ברורות בלוג.
    """
    msg = str(exc) or ""
    # חיפוש ישיר בקוד השגיאה או בהודעת השגיאה
    if "401" in msg or "unauthorized" in msg.lower() or "invalid" in msg.lower():
        print("❌ Google Auth Error detected: 401 Unauthorized or invalid credentials", file=sys.stderr)
        print(f"   Details: {msg}", file=sys.stderr)
        print("   Suggestion: Verify GOOGLE_CREDENTIALS_JSON and that the Service Account has access to the spreadsheet.", file=sys.stderr)
    elif "403" in msg or "forbidden" in msg.lower() or "access" in msg.lower():
        print("❌ Google Auth Error detected: 403 Forbidden or insufficient permissions", file=sys.stderr)
        print(f"   Details: {msg}", file=sys.stderr)
        print("   Suggestion: Ensure the Service Account is granted Editor access to the spreadsheet and Drive API is enabled.", file=sys.stderr)
    else:
        # Generic auth/logging
        print("❌ Google API error during client initialization:", file=sys.stderr)
        print(f"   {msg}", file=sys.stderr)

def validate_env():
    """
    בדיקת משתני סביבה חיוניים. בנוסף מנסה לאתחל את הלקוח של Google Sheets
    בצורה מבוקרת כדי לאבחן בעיות הרשאה מוקדם בתהליך ה-startup.
    """
    required_vars = {
        "TELEGRAM_BOT_TOKEN": TOKEN,
        "WEBHOOK_URL": WEBHOOK_URL,
        "GOOGLE_SHEETS_SPREADSHEET_ID": GOOGLE_SHEETS_SPREADSHEET_ID,
        "GOOGLE_CREDENTIALS_JSON": GOOGLE_CREDENTIALS_JSON,
    }
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        raise Exception(f"Missing required ENV variables: {', '.join(missing)}")

    # Try a lightweight initialization of the sheets client to detect auth/permission issues early.
    try:
        # sheets_service is an instance; call its init method to force auth attempt and catch errors.
        # The method name in the service is _init_client (instance method).
        if hasattr(sheets_service, "_init_client"):
            sheets_service._init_client()
        else:
            # defensive fallback: try to call a public method that triggers lazy init
            try:
                sheets_service.smart_validate_sheets()
            except Exception as inner_exc:
                _log_google_auth_issue(inner_exc)
                raise

        # Try a harmless call to confirm access
        try:
            sp = getattr(sheets_service, "_spreadsheet", None)
            if sp and getattr(sp, "_properties", None):
                title = sp._properties.get("title", "<unknown>")
                print(f"✔ Google Sheets access verified for spreadsheet: {title}")
            else:
                # fallback: try to list worksheets (may raise API errors)
                try:
                    _ = sheets_service._spreadsheet.worksheets()
                    print("✔ Google Sheets access verified (worksheets listed).")
                except Exception as inner_exc:
                    _log_google_auth_issue(inner_exc)
                    raise
        except Exception as inner_exc:
            _log_google_auth_issue(inner_exc)
            raise
    except Exception as e:
        # If any exception occurs during client init, analyze and raise a clear error
        _log_google_auth_issue(e)
        # Re-raise to let startup fail with clear logs
        raise

# ===============================
# Startup – טעינת הבוט
# ===============================

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting bot initialization...")

    try:
        validate_env()
        print("✔ ENV validation passed")
    except Exception as e:
        print(f"❌ ENV validation failed: {e}", file=sys.stderr)
        # print traceback for deeper debugging
        traceback.print_exc()
        raise

    print("🔍 Running Smart Validation on Google Sheets...")
    try:
        # smart_validate_sheets will also use the initialized client
        sheets_service.smart_validate_sheets()
        print("✔ Sheets validated successfully")
    except Exception as e:
        print("❌ CRITICAL: Smart Validation failed!", file=sys.stderr)
        traceback.print_exc()
        print("⚠️ Continuing startup WITHOUT sheet validation. Be aware some features may fail at runtime.", file=sys.stderr)

    print("🔧 Initializing bot handlers...")

    # ConversationHandler הראשי
    conv_handler = bot_handlers.get_conversation_handler()
    application.add_handler(conv_handler)

    # --- Callback handlers בסדר נכון ---
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

    application.add_handler(CallbackQueryHandler(
        bot_handlers.handle_start_callback_entry,
        pattern=rf"^{CALLBACK_START_SLIDE}:|^{CALLBACK_START_SOCI}$|^{CALLBACK_START_FINISH}$"
    ))

    application.add_handler(CallbackQueryHandler(
        bot_handlers.handle_menu_callback
    ))
    application.add_handler(CommandHandler("admin", admin_menu))
    # --- פקודות כלליות ---
    application.add_handler(CommandHandler("start", bot_handlers.start))
    application.add_handler(CommandHandler("menu", bot_handlers.menu_command))
    application.add_handler(CommandHandler("help", bot_handlers.all_commands))
    application.add_handler(CommandHandler("myid", bot_handlers.my_id))
    application.add_handler(CommandHandler("groupid", bot_handlers.group_id))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))

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
    application.add_handler(CommandHandler("backup_sheets", backup_sheets_cmd))

    # --- פקודות אדמין – חיפוש ורשימות ---
    application.add_handler(CommandHandler("find_user", find_user))
    application.add_handler(CommandHandler("find_expert", find_expert))
    application.add_handler(CommandHandler("find_position", find_position))
    application.add_handler(CommandHandler("list_approved_experts", list_approved_experts))
    application.add_handler(CommandHandler("list_rejected_experts", list_rejected_experts))
    application.add_handler(CommandHandler("list_supporters", list_supporters))
    application.add_handler(CommandHandler("admin_menu", admin_menu))

    # --- פקודות אדמין – שידור ---
    application.add_handler(CommandHandler("broadcast_supporters", broadcast_supporters))
    application.add_handler(CommandHandler("broadcast_experts", broadcast_experts))

    # --- פקודות אדמין – Monitoring ---
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("hourly_stats", hourly_stats_command))
    application.add_handler(CommandHandler("export_metrics", export_metrics_command))

    # --- תרומות ---
    application.add_handler(CommandHandler("check_donation", check_donation_status))

    # --- פקודות לא מוכרות ---
    application.add_handler(MessageHandler(filters.COMMAND, bot_handlers.unknown_command))

    # --- image handlers (photos / animations) enqueued to JobQueue ---
    application.add_handler(MessageHandler(filters.PHOTO, image_handlers.handle_photo_message))
    application.add_handler(MessageHandler(filters.ANIMATION | filters.Document.IMAGE, image_handlers.handle_animation_message))
    # --- פקודות אדמין – Monitoring ---
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("stats", quick_stats_command)) # שורה חדשה להדבקה
    application.add_handler(CommandHandler("hourly_stats", hourly_stats_command))
    # --- הפעלת הבוט ---
    await application.initialize()
    await application.start()

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
    from datetime import time
    if getattr(application, "job_queue", None) is not None:
        try:
            application.job_queue.run_daily(
                cleanup_monitoring_job,
                time=time(hour=0, minute=5)
            )
            print("✔ Cleanup job scheduled with JobQueue")
        except Exception as e:
            print(f"⚠ Failed to schedule cleanup job: {e}", file=sys.stderr)
    else:
        print("⚠ JobQueue not available. Skipping scheduled cleanup job.", file=sys.stderr)

    print("🤖 Bot initialized and running!")

async def cleanup_monitoring_job(context):
    """
    ניקוי נתונים ישנים - רץ פעם ביום
    """
    monitoring.cleanup_old_data(days_to_keep=7)
    print("✔ Monitoring data cleanup completed")

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
        # לוג בסיסי של ה‑payload (לא מדפיסים יותר מדי כדי לא לחרוג מגבולות)
        print("🔔 Incoming webhook payload (truncated 200 chars):")
        print(text[:200])

        data = await request.json()
        update = Update.de_json(data, application.bot)

        if update:
            # מעקב אחרי הודעה
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
    return {
        "status": "healthy",
        "bot_username": application.bot.username if application.bot else None,
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
    return {
        "service": "Campaign1 Bot",
        "version": "2.0.0",
        "status": "running",
        "bot": application.bot.username if application.bot else None,
    }


