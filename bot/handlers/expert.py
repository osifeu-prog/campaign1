from telegram import Update
from telegram.ext import ContextTypes
from services.sheets import append_row
from services.ai import analyze_expert_request


async def expert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = " ".join(context.args).strip()

    if not description:
        await update.message.reply_text(
            "אנא צרף תיאור קצר של תחום מומחיותך לאחר הפקודה /expert"
        )
        return

    user = update.effective_user
    username = user.username or ""

    analysis = analyze_expert_request(description)

    append_row(
        "Experts",
        [
            user.id,
            user.full_name,
            username,
            description,
            "pending",
            analysis,
        ],
    )

    append_row(
        "Logs",
        [user.id, "expert_request"],
    )

    await update.message.reply_text(
        "בקשתך כמומחה התקבלה.\n"
        "היא נמצאת כעת בבחינה מקצועית."
    )
