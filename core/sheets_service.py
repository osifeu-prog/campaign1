import gspread
import os, json
from oauth2client.service_account import ServiceAccountCredentials

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")

def get_client():
    creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    return gspread.authorize(creds)

def get_sheet(sheet_name: str):
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID)
    return sheet.worksheet(sheet_name)
