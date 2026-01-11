import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("campaign-bot")

services/sheets.py
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from services.logger import logger
from config.settings import (
    GOOGLE_CREDENTIALS_JSON,
    GOOGLE_SHEETS_SPREADSHEET_ID,
)

if not GOOGLE_CREDENTIALS_JSON:
    raise RuntimeError("GOOGLE_CREDENTIALS_JSON is not set")

if not GOOGLE_SHEETS_SPREADSHEET_ID:
    raise RuntimeError("GOOGLE_SHEETS_SPREADSHEET_ID is not set")

_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

_creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
_creds = ServiceAccountCredentials.from_json_keyfile_dict(_creds_dict, _SCOPE)
_client = gspread.authorize(_creds)
_spreadsheet = _client.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)


def append_row(sheet_name: str, row: list):
    try:
        ws = _spreadsheet.worksheet(sheet_name)
        ws.append_row(row)
    except Exception as e:
        logger.error(f"Google Sheets error [{sheet_name}]: {e}")
