import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "service_account.json", SCOPE
    )
    return gspread.authorize(creds)

def get_sheet(tab_name: str):
    client = get_client()
    sheet = client.open_by_key(SHEET_ID)
    return sheet.worksheet(tab_name)
