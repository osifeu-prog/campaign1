import io
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, 
    ConversationHandler, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters
)

# ייבוא השירותים החדשים
from bot.services.db_service import DBService
from bot.core.image_service import ImageService
from bot.core.telemetry import telemetry
from bot.core.locale_service import LocaleService

# אתחול שירותים
db = DBService()
locale = LocaleService()
logger = logging.getLogger(__name__)

# הגדרת מצבים לשיחה (States)
CHOOSING, TYPING_REPLY, PHOTO_UPLOAD = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """פקודת התחלה - רישום משתמש ב-DB ושליחת הודעת פתיחה"""
    user = update.effective_user
    
    # רישום/עדכון משתמש בבסיס הנתונים
    db.add_user({
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": "supporter"
    })
    
    telemetry.track(user.id, "start_command")
    
    welcome_text = (
        f"שלום {user.first_name}!\n"
        "ברוך הבא למערכת של תנועת אחדות.\n\n"
        "📸 **חדש:** שלח לי תמונה ואני אתאים אותה עבורך לגודל 640x360 פיקסלים!"
    )
    
    await update.message.reply_text(welcome_text)
    return CHOOSING

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מקבל תמונה מהמשתמש, מעבד אותה ומחזיר אותה"""
    user = update.effective_user
    
    try:
        # הודעת המתנה
        status_msg = await update.message.reply_text("מעבד את התמונה, רק רגע... ⏳")
        
        # הורדת התמונה (הגרסה הכי איכותית ברשימה)
        photo_file = await update.message.photo[-1].get_file()
        image_bytearray = await photo_file.download_as_bytearray()
        
        # שימוש בשירות עיבוד התמונה (640x360)
        processed_bio = ImageService.resize_image(bytes(image_bytearray), (640, 360))
        
        # שליחה חזרה למשתמש
        await update.message.reply_photo(
            photo=processed_bio,
            caption="✅ התמונה עובדה בהצלחה לגודל 640x360 פיקסלים."
        )
        
        # מחיקת הודעת הסטטוס
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"Error processing image for user {user.id}: {e}")
        await update.message.reply_text("מצטער, אירעה שגיאה בעיבוד התמונה. וודא ששלחת קובץ תמונה תקין.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ביטול פעולה נוכחית"""
    await update.message.reply_text(
        "הפעולה בוטלה.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def get_main_conv_handler():
    """מנהל את השיחה המרכזית של הבוט"""
    return ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                # כאן תוכל להוסיף כפתורי תפריט נוספים
                MessageHandler(filters.PHOTO, handle_image),
            ],
            PHOTO_UPLOAD: [
                MessageHandler(filters.PHOTO, handle_image)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=True # תיקון האזהרה מהלוגים
    )

# אנדלר נפרד לתמונות שנשלחות מחוץ לשיחה מוגדרת (אופציונלי)
image_handler = MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_image)
