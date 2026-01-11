
from services.sheets import add_expert

async def expert(update, context):
    add_expert(update.effective_user)
    await update.message.reply_text("בקשת מומחה נשלחה לאישור")
