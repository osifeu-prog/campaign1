import os
import json
from typing import Dict, List
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
USERS_SHEET_NAME = os.getenv("USERS_SHEET_NAME", "Users")
EXPERTS_SHEET_NAME = os.getenv("EXPERTS_SHEET_NAME", "Experts")

_scopes = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_sheets_service():
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise RuntimeError("GOOGLE_CREDENTIALS_JSON not set")

    info = json.loads(creds_json)
    credentials = Credentials.from_service_account_info(info, scopes=_scopes)
    service = build("sheets", "v4", credentials=credentials)
    return service


def _append_row(sheet_name: str, values: List):
    service = _get_sheets_service()
    range_name = f"{sheet_name}!A:Z"
    body = {"values": [values]}
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()


def append_user_row(data: Dict):
    values = [
        str(data.get("user_id", "")),
        str(data.get("username", "")),
        str(data.get("full_name_telegram", "")),
        str(data.get("role", "")),
        str(data.get("city", "")),
        str(data.get("email", "")),
        str(data.get("referrer", "")),
        str(data.get("created_at", "")),
    ]
    _append_row(USERS_SHEET_NAME, values)


def append_expert_row(data: Dict):
    values = [
        str(data.get("user_id", "")),
        str(data.get("expert_full_name", "")),
        str(data.get("expert_field", "")),
        str(data.get("expert_experience", "")),
        str(data.get("expert_position", "")),
        str(data.get("expert_links", "")),
        str(data.get("expert_why", "")),
        str(data.get("created_at", "")),
    ]
    _append_row(EXPERTS_SHEET_NAME, values)
