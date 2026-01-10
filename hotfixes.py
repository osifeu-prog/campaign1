# hotfixes.py
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
    pass

try:
    import services.sheets_service as ss
    if not hasattr(ss, "sheets_service"):
        ss.sheets_service = None
    if not hasattr(ss, "_degraded"):
        ss._degraded = False
except Exception:
    pass
