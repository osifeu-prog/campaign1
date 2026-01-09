import os
import json
from typing import Dict, List, Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
USERS_SHEET_NAME = os.getenv("USERS_SHEET_NAME", "Users")
EXPERTS_SHEET_NAME = os.getenv("EXPERTS_SHEET_NAME", "Experts")
POSITIONS_SHEET_NAME = os.getenv("POSITIONS_SHEET_NAME", "Positions")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ------------------ INTERNAL CACHES & SERVICE ------------------

_service = None  # Singleton ל-Google Sheets service

_experts_rows_cache: Optional[List[List[str]]] = None  # rows גולמיים מה-Experts (כולל header)
_positions_cache: Optional[List[Dict[str, str]]] = None  # רשימת dicts כמו ש-get_positions מחזיר
_users_rows_cache: Optional[List[List[str]]] = None  # rows גולמיים מ-Users (אם נשתמש)


def _debug(msg: str):
    # לוג פנימי פשוט, אפשר לכבות אם תרצה
    print(f"[sheets_service] {msg}")


def _invalidate_experts_cache():
    global _experts_rows_cache
    _experts_rows_cache = None
    _debug("Experts cache invalidated")


def _invalidate_positions_cache():
    global _positions_cache
    _positions_cache = None
    _debug("Positions cache invalidated")


def _invalidate_users_cache():
    global _users_rows_cache
    _users_rows_cache = None
    _debug("Users cache invalidated")


# ------------------ SERVICE ------------------

def get_service():
    global _service

    if _service is not None:
        return _service

    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise RuntimeError("GOOGLE_CREDENTIALS_JSON is missing")

    info = json.loads(creds_json)
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    _service = build("sheets", "v4", credentials=credentials)
    _debug("Google Sheets service initialized")
    return _service


def append_row(sheet_name: str, values: List):
    service = get_service()
    range_name = f"{sheet_name}!A:Z"
    body = {"values": [values]}
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()
    _debug(f"Append row to {sheet_name}: {values}")


def batch_update_values(data: List[Dict[str, List[List[str]]]]):
    """
    data: list של dictים בצורה:
    {"range": "Sheet!A1:B1", "values": [[...]]}
    """
    if not data:
        return

    service = get_service()
    body = {
        "valueInputOption": "RAW",
        "data": data,
    }
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()
    _debug(f"Batch update: {len(data)} ranges")


# ------------------ USERS ------------------

def _load_users_rows() -> List[List[str]]:
    global _users_rows_cache

    if _users_rows_cache is not None:
        return _users_rows_cache

    service = get_service()
    range_name = f"{USERS_SHEET_NAME}!A:I"

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()

    rows = result.get("values", []) or []
    _users_rows_cache = rows
    _debug(f"Users rows loaded: {len(rows)}")
    return rows


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
    append_row(USERS_SHEET_NAME, values)
    _invalidate_users_cache()


def get_supporter_by_id(user_id: str) -> Optional[Dict[str, str]]:
    """
    מחזיר תומך מתוך טבלת Users לפי user_id.
    """
    rows = _load_users_rows()
    if not rows or len(rows) < 2:
        return None

    header = rows[0]
    for row in rows[1:]:
        if row and row[0] == str(user_id):
            # התאמה ל-header
            data = {}
            for idx, col in enumerate(row):
                key = header[idx] if idx < len(header) else f"col_{idx}"
                data[key] = col
            return data

    return None


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
    append_row(EXPERTS_SHEET_NAME, values)
    _invalidate_experts_cache()


def _load_experts_rows() -> List[List[str]]:
    """
    טוען את כל שורות המומחים מהגיליון, עם cache.
    השורה הראשונה היא header, השאר נתונים.
    """
    global _experts_rows_cache

    if _experts_rows_cache is not None:
        return _experts_rows_cache

    service = get_service()
    range_name = f"{EXPERTS_SHEET_NAME}!A:J"

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()

    rows = result.get("values", []) or []
    _experts_rows_cache = rows
    _debug(f"Experts rows loaded: {len(rows)}")
    return rows


def update_expert_status(user_id: str, new_status: str):
    service = get_service()
    range_name = f"{EXPERTS_SHEET_NAME}!A:J"

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()

    rows = result.get("values", []) or []
    if not rows:
        return

    for idx, row in enumerate(rows[1:], start=2):
        if row and row[0] == str(user_id):
            update_range = f"{EXPERTS_SHEET_NAME}!I{idx}:I{idx}"
            body = {"values": [[new_status]]}
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=update_range,
                valueInputOption="RAW",
                body=body,
            ).execute()
            _debug(f"Expert {user_id} status updated to {new_status}")
            break

    _invalidate_experts_cache()


def update_expert_group_link(user_id: str, group_link: str):
    service = get_service()
    range_name = f"{EXPERTS_SHEET_NAME}!A:J"

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()

    rows = result.get("values", []) or []
    if not rows:
        return

    for idx, row in enumerate(rows[1:], start=2):
        if row and row[0] == str(user_id):
            update_range = f"{EXPERTS_SHEET_NAME}!J{idx}:J{idx}"
            body = {"values": [[group_link]]}
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=update_range,
                valueInputOption="RAW",
                body=body,
            ).execute()
            _debug(f"Expert {user_id} group_link updated")
            break

    _invalidate_experts_cache()


def get_expert_group_link(user_id: str) -> str:
    rows = _load_experts_rows()
    if not rows:
        return ""

    for row in rows[1:]:
        if row and row[0] == str(user_id):
            return row[9] if len(row) > 9 else ""
    return ""


def get_experts_pending() -> List[Dict[str, str]]:
    """
    מחזיר רשימת מומחים במצב 'pending' כ-list של dicts.
    """
    rows = _load_experts_rows()
    experts: List[Dict[str, str]] = []

    if not rows or len(rows) < 2:
        return experts

    for row in rows[1:]:
        # עמודה I (אינדקס 8) = status
        if len(row) > 8 and row[8] == "pending":
            experts.append({
                "user_id": row[0] if len(row) > 0 else "",
                "expert_full_name": row[1] if len(row) > 1 else "",
                "expert_field": row[2] if len(row) > 2 else "",
                "expert_experience": row[3] if len(row) > 3 else "",
                "expert_position": row[4] if len(row) > 4 else "",
                "expert_links": row[5] if len(row) > 5 else "",
                "expert_why": row[6] if len(row) > 6 else "",
                "created_at": row[7] if len(row) > 7 else "",
            })

    return experts


def get_expert_by_id(user_id: str) -> Optional[Dict[str, str]]:
    """
    מחזיר מומחה לפי user_id כ-dict, כולל status ו-group_link.
    """
    rows = _load_experts_rows()
    if not rows or len(rows) < 2:
        return None

    header = rows[0]
    for row in rows[1:]:
        if row and row[0] == str(user_id):
            data: Dict[str, str] = {}
            for idx, col in enumerate(row):
                key = header[idx] if idx < len(header) else f"col_{idx}"
                data[key] = col
            return data

    return None


def get_expert_status(user_id: str) -> Optional[str]:
    """
    מחזיר את הסטטוס של מומחה: pending / approved / rejected או None אם לא קיים.
    """
    rows = _load_experts_rows()
    if not rows or len(rows) < 2:
        return None

    for row in rows[1:]:
        if row and row[0] == str(user_id):
            return row[8] if len(row) > 8 else None
    return None


def get_expert_position(user_id: str) -> Optional[str]:
    """
    מחזיר את מספר המקום שהמומחה בחר (מתוך עמודה expert_position).
    """
    rows = _load_experts_rows()
    if not rows or len(rows) < 2:
        return None

    for row in rows[1:]:
        if row and row[0] == str(user_id):
            return row[4] if len(row) > 4 else None
    return None


# ------------------ POSITIONS ------------------

def init_positions():
    service = get_service()
    range_name = f"{POSITIONS_SHEET_NAME}!A:E"

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()

    rows = result.get("values", []) or []

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
        _debug("Positions sheet initialized")

    _invalidate_positions_cache()


def _load_positions() -> List[Dict[str, str]]:
    """
    טוען את כל המקומות כ-list של dicts, עם cache.
    """
    global _positions_cache

    if _positions_cache is not None:
        return _positions_cache

    service = get_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{POSITIONS_SHEET_NAME}!A:E"
    ).execute()

    rows = result.get("values", []) or []
    positions: List[Dict[str, str]] = []

    if rows:
        for row in rows[1:]:
            positions.append({
                "position_id": row[0] if len(row) > 0 else "",
                "title": row[1] if len(row) > 1 else "",
                "description": row[2] if len(row) > 2 else "",
                "expert_user_id": row[3] if len(row) > 3 else "",
                "assigned_at": row[4] if len(row) > 4 else "",
            })

    _positions_cache = positions
    _debug(f"Positions loaded: {len(positions)}")
    return positions


def get_positions() -> List[Dict[str, str]]:
    return _load_positions()


def get_position(position_id: str) -> Optional[Dict[str, str]]:
    for pos in _load_positions():
        if pos["position_id"] == str(position_id):
            return pos
    return None


def position_is_free(position_id: str) -> bool:
    pos = get_position(position_id)
    if not pos:
        return False
    return pos["expert_user_id"] == ""


def get_positions_free() -> List[Dict[str, str]]:
    """
    מחזיר רשימת מקומות פנויים בלבד.
    """
    return [p for p in _load_positions() if not p.get("expert_user_id")]


def get_positions_taken() -> List[Dict[str, str]]:
    """
    מחזיר רשימת מקומות תפוסים בלבד.
    """
    return [p for p in _load_positions() if p.get("expert_user_id")]


def assign_position(position_id: str, user_id: str, timestamp: str):
    service = get_service()

    positions = _load_positions()
    row_index = None

    for i, pos in enumerate(positions, start=2):
        if pos["position_id"] == str(position_id):
            row_index = i
            break

    if row_index is None:
        raise ValueError("Position not found")

    update_range = f"{POSITIONS_SHEET_NAME}!D{row_index}:E{row_index}"
    body = {"values": [[str(user_id), timestamp]]}

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=update_range,
        valueInputOption="RAW",
        body=body
    ).execute()

    _debug(f"Position {position_id} assigned to {user_id}")
    _invalidate_positions_cache()


def reset_position(position_id: str):
    """
    מאפס מקום אחד: expert_user_id ו-assigned_at.
    """
    service = get_service()

    positions = _load_positions()
    row_index = None

    for i, pos in enumerate(positions, start=2):
        if pos["position_id"] == str(position_id):
            row_index = i
            break

    if row_index is None:
        raise ValueError("Position not found")

    update_range = f"{POSITIONS_SHEET_NAME}!D{row_index}:E{row_index}"
    body = {"values": [["", ""]]}

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=update_range,
        valueInputOption="RAW",
        body=body
    ).execute()

    _debug(f"Position {position_id} reset")
    _invalidate_positions_cache()


def reset_all_positions():
    """
    מאפס את כל המקומות (עמודות expert_user_id + assigned_at).
    שימושי לאדמין בלבד.
    """
    service = get_service()
    positions = _load_positions()
    if not positions:
        return

    data = []
    # כל השורות מתחילות מאינדקס 2 (header בשורה 1)
    for i, pos in enumerate(positions, start=2):
        rng = f"{POSITIONS_SHEET_NAME}!D{i}:E{i}"
        data.append({
            "range": rng,
            "values": [["", ""]],
        })

    batch_update_values(data)
    _debug("All positions reset")
    _invalidate_positions_cache()
