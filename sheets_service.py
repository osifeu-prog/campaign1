import os
import json
from datetime import datetime
from typing import List, Dict, Optional

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
USERS_SHEET_NAME = os.getenv("USERS_SHEET_NAME", "Users")
EXPERTS_SHEET_NAME = os.getenv("EXPERTS_SHEET_NAME", "Experts")
POSITIONS_SHEET_NAME = os.getenv("POSITIONS_SHEET_NAME", "Positions")

GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

if not GOOGLE_CREDENTIALS_JSON:
    raise Exception("Missing GOOGLE_CREDENTIALS_JSON env variable")

creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
gc = gspread.authorize(credentials)


def _open_sheet(name: str):
    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
        return sh.worksheet(name)
    except Exception as e:
        print(f"Failed to open sheet {name}: {e}")
        raise


users_sheet = _open_sheet(USERS_SHEET_NAME)
experts_sheet = _open_sheet(EXPERTS_SHEET_NAME)
positions_sheet = _open_sheet(POSITIONS_SHEET_NAME)


def append_user_row(row: Dict):
    users_sheet.append_row([
        row.get("user_id", ""),
        row.get("username", ""),
        row.get("full_name_telegram", ""),
        row.get("role", ""),
        row.get("city", ""),
        row.get("email", ""),
        row.get("referrer", ""),
        row.get("joined_via_expert_id", ""),
        row.get("created_at", ""),
    ])


def get_supporter_by_id(user_id: str) -> Optional[Dict]:
    rows = users_sheet.get_all_records()
    for row in rows:
        if str(row.get("user_id")) == str(user_id):
            return row
    return None


def append_expert_row(row: Dict):
    experts_sheet.append_row([
        row.get("user_id", ""),
        row.get("expert_full_name", ""),
        row.get("expert_field", ""),
        row.get("expert_experience", ""),
        row.get("expert_position", ""),
        row.get("expert_links", ""),
        row.get("expert_why", ""),
        row.get("created_at", ""),
        row.get("group_link", ""),
        "pending",
    ])


def get_expert_by_id(user_id: str) -> Optional[Dict]:
    rows = experts_sheet.get_all_records()
    for row in rows:
        if str(row.get("user_id")) == str(user_id):
            return row
    return None


def get_expert_status(user_id: str) -> Optional[str]:
    rows = experts_sheet.get_all_records()
    for row in rows:
        if str(row.get("user_id")) == str(user_id):
            return row.get("status")
    return None


def update_expert_status(user_id: str, status: str):
    rows = experts_sheet.get_all_records()
    for idx, row in enumerate(rows, start=2):
        if str(row.get("user_id")) == str(user_id):
            experts_sheet.update_cell(idx, 10, status)
            return


def get_expert_position(user_id: str) -> Optional[str]:
    rows = experts_sheet.get_all_records()
    for row in rows:
        if str(row.get("user_id")) == str(user_id):
            return row.get("expert_position")
    return None


def get_expert_group_link(user_id: str) -> Optional[str]:
    rows = experts_sheet.get_all_records()
    for row in rows:
        if str(row.get("user_id")) == str(user_id):
            return row.get("group_link")
    return None


def update_expert_group_link(user_id: str, link: str):
    rows = experts_sheet.get_all_records()
    for idx, row in enumerate(rows, start=2):
        if str(row.get("user_id")) == str(user_id):
            experts_sheet.update_cell(idx, 9, link)
            return


def get_experts_pending() -> List[Dict]:
    rows = experts_sheet.get_all_records()
    return [row for row in rows if row.get("status") == "pending"]


def get_positions() -> List[Dict]:
    return positions_sheet.get_all_records()


def get_position(position_id: str) -> Optional[Dict]:
    rows = positions_sheet.get_all_records()
    for row in rows:
        if str(row.get("position_id")) == str(position_id):
            return row
    return None


def position_is_free(position_id: str) -> bool:
    pos = get_position(position_id)
    if not pos:
        return False
    return pos.get("expert_user_id") in ("", None)


def assign_position(position_id: str, user_id: str, timestamp: str):
    rows = positions_sheet.get_all_records()
    for idx, row in enumerate(rows, start=2):
        if str(row.get("position_id")) == str(position_id):
            positions_sheet.update_cell(idx, 4, user_id)
            positions_sheet.update_cell(idx, 5, timestamp)
            return


def reset_position(position_id: str):
    rows = positions_sheet.get_all_records()
    for idx, row in enumerate(rows, start=2):
        if str(row.get("position_id")) == str(position_id):
            positions_sheet.update_cell(idx, 4, "")
            positions_sheet.update_cell(idx, 5, "")
            return
    raise ValueError("Position not found")


def reset_all_positions():
    rows = positions_sheet.get_all_records()
    for idx, row in enumerate(rows, start=2):
        positions_sheet.update_cell(idx, 4, "")
        positions_sheet.update_cell(idx, 5, "")

def validate_headers(sheet, expected_headers):
    """
    בודק שהכותרות בשורה 1:
    - קיימות
    - ייחודיות
    - תואמות למה שהבוט צריך
    """
    headers = sheet.row_values(1)

    # בדיקה: האם יש כפילויות
    if len(headers) != len(set(headers)):
        raise ValueError(f"Duplicate headers found in sheet '{sheet.title}'")

    # בדיקה: האם כל הכותרות הנדרשות קיימות
    missing = [h for h in expected_headers if h not in headers]
    if missing:
        raise ValueError(
            f"Missing required headers in sheet '{sheet.title}': {missing}"
        )

    return True


def validate_all_sheets():
    """
    בודק את כל הגיליונות: Users, Experts, Positions
    """
    # כותרות תקינות עבור כל גיליון
    expected_users = [
        "user_id", "username", "full_name_telegram", "role",
        "city", "email", "referrer", "joined_via_expert_id", "created_at"
    ]

    expected_experts = [
        "user_id", "expert_full_name", "expert_field", "expert_experience",
        "expert_position", "expert_links", "expert_why",
        "created_at", "status", "group_link"
    ]

    expected_positions = [
        "position_id", "title", "description",
        "expert_user_id", "assigned_at"
    ]

    # בדיקה בפועל
    validate_headers(users_sheet, expected_users)
    validate_headers(experts_sheet, expected_experts)
    validate_headers(positions_sheet, expected_positions)

    print("✔ All sheets validated successfully")
