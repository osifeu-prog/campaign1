import os
import json
from typing import Dict, List
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
USERS_SHEET_NAME = os.getenv("USERS_SHEET_NAME", "Users")
EXPERTS_SHEET_NAME = os.getenv("EXPERTS_SHEET_NAME", "Experts")
POSITIONS_SHEET_NAME = os.getenv("POSITIONS_SHEET_NAME", "Positions")

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


# ------------------ USERS ------------------

def append_user_row(data: Dict):
    values = [
        str(data.get("user_id", "")),
        str(data.get("username", "")),
        str(data.get("full_name_telegram", "")),
        str(data.get("role", "")),
        str(data.get("city", "")),
        str(data.get("email", "")),
        str(data.get("referrer", "")),
        str(data.get("joined_via_expert_id", "")),
        str(data.get("created_at", "")),
    ]
    _append_row(USERS_SHEET_NAME, values)


# ------------------ EXPERTS ------------------

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
        "pending",
        str(data.get("group_link", "")),
    ]
    _append_row(EXPERTS_SHEET_NAME, values)


def update_expert_status(user_id: str, new_status: str):
    service = _get_sheets_service()
    range_name = f"{EXPERTS_SHEET_NAME}!A:J"

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()

    rows = result.get("values", [])
    if not rows:
        return

    for idx, row in enumerate(rows[1:], start=2):
        if len(row) > 0 and row[0] == str(user_id):
            status_range = f"{EXPERTS_SHEET_NAME}!I{idx}:I{idx}"
            body = {"values": [[new_status]]}
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=status_range,
                valueInputOption="RAW",
                body=body,
            ).execute()
            break


def update_expert_group_link(user_id: str, group_link: str):
    service = _get_sheets_service()
    range_name = f"{EXPERTS_SHEET_NAME}!A:J"

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()

    rows = result.get("values", [])
    if not rows:
        return

    for idx, row in enumerate(rows[1:], start=2):
        if len(row) > 0 and row[0] == str(user_id):
            group_range = f"{EXPERTS_SHEET_NAME}!J{idx}:J{idx}"
            body = {"values": [[group_link]]}
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=group_range,
                valueInputOption="RAW",
                body=body,
            ).execute()
            break


def get_expert_group_link(user_id: str) -> str:
    service = _get_sheets_service()
    range_name = f"{EXPERTS_SHEET_NAME}!A:J"

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()

    rows = result.get("values", [])
    if not rows:
        return ""

    for row in rows[1:]:
        if len(row) > 0 and row[0] == str(user_id):
            return row[9] if len(row) > 9 else ""
    return ""


# ------------------ POSITIONS ------------------

def init_positions():
    service = _get_sheets_service()
    range_name = f"{POSITIONS_SHEET_NAME}!A:E"

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()

    rows = result.get("values", [])

    if len(rows) < 2:
        header = ["position_id", "title", "description", "expert_user_id", "assigned_at"]
        data_rows = []
        for i in range(1, 122):
            data_rows.append([
                str(i),
                f"Position {i}",
                "",
                "",
                "",
            ])

        body = {"values": [header] + data_rows}
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()


def get_positions():
    service = _get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{POSITIONS_SHEET_NAME}!A:E"
    ).execute()

    rows = result.get("values", [])
    positions = []

    if not rows:
        return positions

    for row in rows[1:]:
        positions.append({
            "position_id": row[0] if len(row) > 0 else "",
            "title": row[1] if len(row) > 1 else "",
            "description": row[2] if len(row) > 2 else "",
            "expert_user_id": row[3] if len(row) > 3 else "",
            "assigned_at": row[4] if len(row) > 4 else "",
        })

    return positions


def get_position(position_id: str):
    for pos in get_positions():
        if pos["position_id"] == str(position_id):
            return pos
    return None


def position_is_free(position_id: str) -> bool:
    pos = get_position(position_id)
    if not pos:
        return False
    return pos["expert_user_id"] == ""


def assign_position(position_id: str, user_id: str, timestamp: str):
    service = _get_sheets_service()

    positions = get_positions()
    row_index = None

    for i, pos in enumerate(positions, start=2):
        if pos["position_id"] == str(position_id):
            row_index = i
            break

    if row_index is None:
        raise ValueError("Position not found")

    range_name = f"{POSITIONS_SHEET_NAME}!D{row_index}:E{row_index}"
    body = {"values": [[str(user_id), timestamp]]}

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body=body
    ).execute()
