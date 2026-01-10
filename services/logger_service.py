# services/logger_service.py
import os
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict

from telegram import User
from telegram.ext import ContextTypes

LOG_GROUP_ID = os.getenv("LOG_GROUP_ID", "")


async def log(
    context: ContextTypes.DEFAULT_TYPE,
    message: str,
    user: Optional[User] = None,
    extra: Optional[Dict] = None,
    level: str = "INFO",
    include_traceback: bool = False,
):
    """
    לוג חכם עם context:
    - user: אובייקט משתמש של Telegram
    - extra: מילון עם מידע נוסף (מקום, פעולה, סטטוס וכו')
    - level: רמת לוג (INFO / WARNING / ERROR)
    """

    timestamp = datetime.utcnow().isoformat()

    user_info = ""
    if user:
        user_info = (
            f"[USER] id={user.id}, username=@{user.username}, name={user.full_name}\n"
        )

    extra_info = ""
    if extra:
        for key, value in extra.items():
            extra_info += f"[{key.upper()}] {value}\n"

    tb_info = ""
    if include_traceback:
        tb_info = "[TRACEBACK]\n" + "".join(traceback.format_exc()) + "\n"

    final_message = (
        f"=== LOG ENTRY ===\n"
        f"[TIME] {timestamp}\n"
        f"[LEVEL] {level}\n"
        f"{user_info}"
        f"{extra_info}"
        f"{tb_info}"
        f"[MESSAGE] {message}\n"
        f"=================="
    )

    # הדפסה ל־stdout (Railway logs)
    print(final_message, file=sys.stdout)

    if LOG_GROUP_ID:
        try:
            await context.bot.send_message(
                chat_id=int(LOG_GROUP_ID),
                text=final_message[:4096],
            )
        except Exception as e:
            print("Failed to send log:", e, file=sys.stderr)
