from telegram import Update
from telegram.ext import ContextTypes
from services.sheets import append_row
from services.ai import analyze_expert_request


async def expert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = " ".join(context.args).strip()

    if not description:
        await update.message.reply_text(
            "אנא צרף תיאור קצר של תחום מומחיותך."
        )
        return

    analysis = analyze_expert_request(description)

    append_row(
        "Experts",
        [
            update.effective_user.id,
            update.effective_user.full_name,
            description,
            "pending",
            analysis,
        ],
    )

    await update.message.reply_text(
        "בקשתך כמומחה התקבלה.\n"
        "היא תיבחן על ידי הגורמים המוסמכים."
    )
