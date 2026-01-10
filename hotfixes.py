# hotfixes.py
# Runtime safety shim: add missing aliases and safe placeholders to avoid import-time crashes.
import sys

# 1) Ensure bot_handlers has handle_start_callback_entry alias if start exists
try:
    import bot.handlers.bot_handlers as bh
    if not hasattr(bh, "handle_start_callback_entry") and hasattr(bh, "start"):
        def handle_start_callback_entry(update, context):
            try:
                return bh.start(update, context)
            except Exception:
                return None
        bh.handle_start_callback_entry = handle_start_callback_entry
except Exception:
    # ignore; this is a best-effort shim
    pass

# 2) Ensure services.sheets_service module exists and has a sheets_service attribute placeholder
try:
    import services.sheets_service as ss
    if not hasattr(ss, "sheets_service"):
        ss.sheets_service = None
except Exception:
    # ignore; if services package missing, do not crash
    pass
