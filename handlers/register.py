
from services.sheets import add_user

async def register(update, context):
    add_user(update.effective_user)
    await update.message.reply_text("נרשמת בהצלחה!")
