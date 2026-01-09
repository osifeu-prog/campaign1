import os
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
):
    """
    לוג חכם עם context:
    - user: אובייקט משתמש של Telegram
    - extra: מילון עם מידע נוסף (מקום, פעולה, סטטוס וכו')
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

    final_message = (
        f"=== LOG ENTRY ===\n"
        f"[TIME] {timestamp}\n"
        f"{user_info}"
        f"{extra_info}"
        f"[MESSAGE] {message}\n"
        f"=================="
    )

    print(final_message)

    if LOG_GROUP_ID:
        try:
            await context.bot.send_message(
                chat_id=int(LOG_GROUP_ID),
                text=final_message
            )
        except Exception as e:
            print("Failed to send log:", e)
