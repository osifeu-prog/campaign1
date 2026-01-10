# ===============================
# services/sheets_service.py - משודרג
# ===============================

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import threading
from contextlib import contextmanager

import gspread
from google.oauth2.service_account import Credentials

# ============================================================
#  CONFIG
# ============================================================

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


# ============================================================
#  LOCKS למניעת race conditions
# ============================================================

class SheetLockManager:
    def __init__(self):
        self._locks = {}
        self._main_lock = threading.Lock()
    
    @contextmanager
    def lock_sheet(self, sheet_name: str):
        with self._main_lock:
            if sheet_name not in self._locks:
                self._locks[sheet_name] = threading.Lock()
            sheet_lock = self._locks[sheet_name]
        
        sheet_lock.acquire()
        try:
            yield
        finally:
            sheet_lock.release()

sheet_lock_manager = SheetLockManager()


# ============================================================
#  RETRY DECORATOR
# ============================================================

import time
import functools

def retry_sheets_operation(max_retries=3, base_delay=2.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (gspread.exceptions.APIError, ConnectionError, TimeoutError) as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        raise
                    delay = min(base_delay * (2 ** attempt), 30.0)
                    print(f"⚠️ Retry {attempt + 1}/{max_retries} for {func.__name__} in {delay:.1f}s")
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


# ============================================================
#  HELPERS
# ============================================================

@retry_sheets_operation()
def _open_sheet(name: str):
    sh = gc.open_by_key(SPREADSHEET_ID)
    return sh.worksheet(name)


def get_users_sheet():
    return _open_sheet(USERS_SHEET_NAME)


def get_experts_sheet():
    return _open_sheet(EXPERTS_SHEET_NAME)


def get_positions_sheet():
    return _open_sheet(POSITIONS_SHEET_NAME)


# ============================================================
#  USERS
# ============================================================

@retry_sheets_operation()
def append_user_row(row: Dict[str, Any]):
    with sheet_lock_manager.lock_sheet("Users"):
        sheet = get_users_sheet()
        headers = sheet.row_values(1)
        
        for key in row.keys():
            if key not in headers:
                headers.append(key)
        sheet.update("1:1", [headers])
        
        values = [row.get(h, "") for h in headers]
        sheet.append_row(values)


@retry_sheets_operation()
def get_supporter_by_id(user_id: str) -> Optional[Dict]:
    sheet = get_users_sheet()
    rows = sheet.get_all_records()
    for row in rows:
        if str(row.get("user_id")) == str(user_id):
            return row
    return None


@retry_sheets_operation()
def clear_user_duplicates() -> int:
    with sheet_lock_manager.lock_sheet("Users"):
        sheet = get_users_sheet()
        rows = sheet.get_all_records()
        if not rows:
            return 0

        user_rows: Dict[str, int] = {}
        created_map: Dict[str, datetime] = {}
        to_delete_indices: List[int] = []

        for idx, row in enumerate(rows, start=2):
            uid = str(row.get("user_id", "")).strip()
            if not uid:
                continue

            created_str = str(row.get("created_at", "")).strip()
            try:
                created_dt = datetime.fromisoformat(created_str)
            except Exception:
                created_dt = datetime.min

            if uid not in created_map or created_dt >= created_map[uid]:
                if uid in user_rows:
                    to_delete_indices.append(user_rows[uid])
                created_map[uid] = created_dt
                user_rows[uid] = idx
            else:
                to_delete_indices.append(idx)

        to_delete_indices = sorted(set(to_delete_indices), reverse=True)
        for idx in to_delete_indices:
            sheet.delete_rows(idx)

        return len(to_delete_indices)


# ============================================================
#  EXPERTS
# ============================================================

@retry_sheets_operation()
def append_expert_row(row: Dict[str, Any]):
    with sheet_lock_manager.lock_sheet("Experts"):
        sheet = get_experts_sheet()
        headers = sheet.row_values(1)

        expected_headers = [
            "user_id", "expert_full_name", "expert_field", "expert_experience",
            "expert_position", "expert_links", "expert_why",
            "created_at", "status", "group_link", "supporters_count"
        ]

        for h in expected_headers:
            if h not in headers:
                headers.append(h)

        sheet.update("1:1", [headers])

        base_row = {
            "user_id": row.get("user_id", ""),
            "expert_full_name": row.get("expert_full_name", ""),
            "expert_field": row.get("expert_field", ""),
            "expert_experience": row.get("expert_experience", ""),
            "expert_position": row.get("expert_position", ""),
            "expert_links": row.get("expert_links", ""),
            "expert_why": row.get("expert_why", ""),
            "created_at": row.get("created_at", ""),
            "status": row.get("status", "pending"),
            "group_link": row.get("group_link", ""),
            "supporters_count": row.get("supporters_count", 0),
        }

        values = [base_row.get(h, "") for h in headers]
        sheet.append_row(values)


@retry_sheets_operation()
def get_expert_by_id(user_id: str) -> Optional[Dict]:
    sheet = get_experts_sheet()
    rows = sheet.get_all_records()
    for row in rows:
        if str(row.get("user_id")) == str(user_id):
            return row
    return None


@retry_sheets_operation()
def get_expert_status(user_id: str) -> Optional[str]:
    expert = get_expert_by_id(user_id)
    if not expert:
        return None
    return expert.get("status")


@retry_sheets_operation()
def update_expert_status(user_id: str, status: str):
    with sheet_lock_manager.lock_sheet("Experts"):
        sheet = get_experts_sheet()
        rows = sheet.get_all_records()
        headers = sheet.row_values(1)
        
        # מציאת אינדקס עמודת status
        try:
            status_col = headers.index("status") + 1
        except ValueError:
            status_col = 9
        
        for idx, row in enumerate(rows, start=2):
            if str(row.get("user_id")) == str(user_id):
                sheet.update_cell(idx, status_col, status)
                return


@retry_sheets_operation()
def get_expert_position(user_id: str) -> Optional[str]:
    expert = get_expert_by_id(user_id)
    if not expert:
        return None
    return expert.get("expert_position")


@retry_sheets_operation()
def get_expert_group_link(user_id: str) -> Optional[str]:
    expert = get_expert_by_id(user_id)
    if not expert:
        return None
    return expert.get("group_link")


@retry_sheets_operation()
def update_expert_group_link(user_id: str, link: str):
    with sheet_lock_manager.lock_sheet("Experts"):
        sheet = get_experts_sheet()
        rows = sheet.get_all_records()
        headers = sheet.row_values(1)
        
        try:
            group_link_col = headers.index("group_link") + 1
        except ValueError:
            group_link_col = 10
        
        for idx, row in enumerate(rows, start=2):
            if str(row.get("user_id")) == str(user_id):
                sheet.update_cell(idx, group_link_col, link)
                return


@retry_sheets_operation()
def increment_expert_supporters(expert_user_id: str):
    """
    הגדלת מונה התומכים של מומחה
    """
    with sheet_lock_manager.lock_sheet("Experts"):
        sheet = get_experts_sheet()
        rows = sheet.get_all_records()
        headers = sheet.row_values(1)
        
        try:
            count_col = headers.index("supporters_count") + 1
        except ValueError:
            # אם העמודה לא קיימת, נוסיף אותה
            headers.append("supporters_count")
            sheet.update("1:1", [headers])
            count_col = len(headers)
        
        for idx, row in enumerate(rows, start=2):
            if str(row.get("user_id")) == str(expert_user_id):
                current = int(row.get("supporters_count", 0) or 0)
                sheet.update_cell(idx, count_col, current + 1)
                return


@retry_sheets_operation()
def get_experts_leaderboard() -> List[Dict]:
    """
    קבלת טבלת מובילים של מומחים
    """
    sheet = get_experts_sheet()
    rows = sheet.get_all_records()
    
    # סינון רק מומחים מאושרים
    approved = [r for r in rows if r.get("status") == "approved"]
    
    # מיון לפי מספר תומכים (יורד)
    sorted_experts = sorted(
        approved,
        key=lambda x: int(x.get("supporters_count", 0) or 0),
        reverse=True
    )
    
    return sorted_experts[:20]  # 20 הראשונים


@retry_sheets_operation()
def get_experts_pending() -> List[Dict]:
    sheet = get_experts_sheet()
    rows = sheet.get_all_records()
    return [row for row in rows if row.get("status") == "pending"]


@retry_sheets_operation()
def clear_expert_duplicates() -> int:
    with sheet_lock_manager.lock_sheet("Experts"):
        sheet = get_experts_sheet()
        rows = sheet.get_all_records()
        if not rows:
            return 0

        user_rows: Dict[str, int] = {}
        created_map: Dict[str, datetime] = {}
        to_delete_indices: List[int] = []

        for idx, row in enumerate(rows, start=2):
            uid = str(row.get("user_id", "")).strip()
            if not uid:
                continue

            created_str = str(row.get("created_at", "")).strip()
            try:
                created_dt = datetime.fromisoformat(created_str)
            except Exception:
                created_dt = datetime.min

            if uid not in created_map or created_dt >= created_map[uid]:
                if uid in user_rows:
                    to_delete_indices.append(user_rows[uid])
                created_map[uid] = created_dt
                user_rows[uid] = idx
            else:
                to_delete_indices.append(idx)

        to_delete_indices = sorted(set(to_delete_indices), reverse=True)
        for idx in to_delete_indices:
            sheet.delete_rows(idx)

        return len(to_delete_indices)


# ============================================================
#  POSITIONS
# ============================================================

@retry_sheets_operation()
def get_positions() -> List[Dict]:
    sheet = get_positions_sheet()
    return sheet.get_all_records()


@retry_sheets_operation()
def get_position(position_id: str) -> Optional[Dict]:
    sheet = get_positions_sheet()
    rows = sheet.get_all_records()
    for row in rows:
        if str(row.get("position_id")) == str(position_id):
            return row
    return None


@retry_sheets_operation()
def position_is_free(position_id: str) -> bool:
    pos = get_position(position_id)
    if not pos:
        return False
    expert_id = str(pos.get("expert_user_id", "")).strip()
    return expert_id == ""


@retry_sheets_operation()
def assign_position(position_id: str, user_id: str, timestamp: str):
    with sheet_lock_manager.lock_sheet("Positions"):
        sheet = get_positions_sheet()
        rows = sheet.get_all_records()
        for idx, row in enumerate(rows, start=2):
            if str(row.get("position_id")) == str(position_id):
                sheet.update(f"D{idx}:E{idx}", [[user_id, timestamp]])
                return
        raise ValueError("Position not found")


@retry_sheets_operation()
def reset_position(position_id: str):
    with sheet_lock_manager.lock_sheet("Positions"):
        sheet = get_positions_sheet()
        rows = sheet.get_all_records()
        for idx, row in enumerate(rows, start=2):
            if str(row.get("position_id")) == str(position_id):
                sheet.update(f"D{idx}:E{idx}", [["", ""]])
                return
        raise ValueError("Position not found")


@retry_sheets_operation()
def reset_all_positions():
    with sheet_lock_manager.lock_sheet("Positions"):
        sheet = get_positions_sheet()
        rows = sheet.get_all_records()
        if not rows:
            return
        updates = [["", ""] for _ in rows]
        sheet.update(f"D2:E{len(rows)+1}", updates)


# ============================================================
#  SHEET INFO / VALIDATION (ללא שינוי)
# ============================================================

def get_sheet_info(sheet) -> Dict:
    headers = sheet.row_values(1)
    all_values = sheet.get_all_values()
    rows_count = len(all_values)
    cols_count = max((len(r) for r in all_values), default=0)

    return {
        "title": sheet.title,
        "headers": headers,
        "rows": rows_count,
        "cols": cols_count,
    }


def validate_headers(sheet, expected_headers):
    headers = sheet.row_values(1)

    if len(headers) != len(set(headers)):
        raise ValueError(f"Duplicate headers found in sheet '{sheet.title}'")

    missing = [h for h in expected_headers if h not in headers]
    if missing:
        raise ValueError(
            f"Missing required headers in sheet '{sheet.title}': {missing}"
        )

    return True


def validate_all_sheets():
    users_sheet = get_users_sheet()
    experts_sheet = get_experts_sheet()
    positions_sheet = get_positions_sheet()

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

    validate_headers(users_sheet, expected_users)
    validate_headers(experts_sheet, expected_experts)
    validate_headers(positions_sheet, expected_positions)

    print("✔ All sheets validated successfully")


def auto_fix_headers(sheet, expected_headers):
    headers = sheet.row_values(1)
    fixed = []
    seen = set()

    for h in headers:
        original = h.strip()
        if original == "":
            original = f"unnamed_{len(fixed)+1}"

        new_h = original
        counter = 2
        while new_h in seen:
            new_h = f"{original}_{counter}"
            counter += 1

        fixed.append(new_h)
        seen.add(new_h)

    for h in expected_headers:
        if h not in fixed:
            fixed.append(h)

    sheet.update("1:1", [fixed])
    print(f"✔ Auto-fixed headers for sheet '{sheet.title}'")
    return fixed


def auto_fix_all_sheets():
    users_sheet = get_users_sheet()
    experts_sheet = get_experts_sheet()
    positions_sheet = get_positions_sheet()

    expected_users = [
        "user_id", "username", "full_name_telegram", "role",
        "city", "email", "referrer", "joined_via_expert_id", "created_at"
    ]

    expected_experts = [
        "user_id", "expert_full_name", "expert_field", "expert_experience",
        "expert_position", "expert_links", "expert_why",
        "created_at", "status", "group_link", "supporters_count"
    ]

    expected_positions = [
        "position_id", "title", "description",
        "expert_user_id", "assigned_at"
    ]

    auto_fix_headers(users_sheet, expected_users)
    auto_fix_headers(experts_sheet, expected_experts)
    auto_fix_headers(positions_sheet, expected_positions)

    print("✔ All sheets auto-fixed successfully")


def smart_validate_sheets():
    print("🔍 Running Smart Validation...")

    try:
        validate_all_sheets()
        print("✔ Sheets valid on first check")
        return
    except Exception as e:
        print(f"⚠ Validation failed on first attempt: {e}")
        print("🔧 Attempting auto-fix...")

        try:
            auto_fix_all_sheets()
        except Exception as fix_err:
            print(f"❌ Auto-fix failed: {fix_err}")
            raise Exception("Auto-fix failed, cannot continue")

    try:
        validate_all_sheets()
        print("✔ Sheets valid after auto-fix")
        return
    except Exception as e:
        print(f"❌ Validation failed even after auto-fix: {e}")
        raise Exception(
            "Critical sheet structure error — cannot auto-fix. "
            "Please fix the sheet manually."
        )
