
from telegram.ext import Application
from config.settings import TELEGRAM_BOT_TOKEN


def build_application() -> Application:
    return Application.builder().token(TELEGRAM_BOT_TOKEN).build()

bot/handlers/common.py

from telegram import Update
from telegram.ext import ContextTypes
from services.sheets import append_row


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ברוכים הבאים לשער האזרחי הרשמי.\n\n"
        "מערכת זו נועדה לרישום אזרחים ומומחים, "
        "בבסיס תשתית אזרחית-טכנולוגית שקופה ואחראית."
    )

    append_row(
        "Logs",
        [update.effective_user.id, "start", update.effective_user.username],
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/register – רישום אזרח\n"
        "/expert – בקשת הצטרפות כמומחה\n"
        "/status – בדיקת סטטוס\n"
        "/admin – ניהול (לאדמינים בלבד)"
    )

bot/handlers/user.py
from telegram import Update
from telegram.ext import ContextTypes
from services.sheets import append_row


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    append_row(
        "Users",
        [user.id, user.full_name, user.username or ""],
    )

    append_row(
        "Logs",
        [user.id, "register"],
    )

    await update.message.reply_text(
        "הרישום האזרחי נקלט בהצלחה.\n"
        "תודה על הצטרפותך."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "הפרופיל שלך קיים במערכת.\n"
        "לעדכונים נוספים – פנה לאדמיניסטרציה."
    )

bot/handlers/expert.py
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



bot/handlers/admin.py
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS
from services.sheets import append_row


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ אין לך הרשאות ניהול.")
        return

    append_row(
        "Logs",
        [user.id, "admin_menu"],
    )

    await update.message.reply_text(
        "🛠 תפריט ניהול\n\n"
        "• אישור / דחיית מומחים\n"
        "• ניהול משתמשים\n"
        "• צפייה בלוגים\n\n"
        "מערכת זו נבנתה להתרחבות עתידית."
    )
