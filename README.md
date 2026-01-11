# Campaign Bot – מערכת אזרחית-טכנולוגית

## פריסה (Railway)
1. הגדר ENV VARS:
   - TELEGRAM_BOT_TOKEN
   - WEBHOOK_URL
   - GOOGLE_CREDENTIALS_JSON
   - GOOGLE_SHEETS_SPREADSHEET_ID
   - ADMIN_IDS
   - OPENAI_API_KEY (אופציונלי)

2. התקנה:
   pip install -r requirements.txt

3. השירות מאזין ל:
   POST /webhook

## פקודות
/start – שער כניסה  
/register – רישום אזרח  
/expert – בקשת הצטרפות כמומחה  
/status – בדיקת סטטוס  
/admin – ניהול (אדמינים בלבד)

## זרימה
Telegram  
→ Webhook  
→ FastAPI  
→ python-telegram-bot  
→ Handlers  
→ Google Sheets / AI
