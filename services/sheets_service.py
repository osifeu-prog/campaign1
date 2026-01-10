# services/sheets_service.py
import os
import time
import json
import threading
from typing import List, Dict, Optional, Any
from datetime import datetime
from functools import wraps

import gspread
from google.oauth2.service_account import Credentials

GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
USERS_SHEET_NAME = os.getenv("USERS_SHEET_NAME", "Telegram Leads")
EXPERTS_SHEET_NAME = os.getenv("EXPERTS_SHEET_NAME", "Experts")
POSITIONS_SHEET_NAME = os.getenv("POSITIONS_SHEET_NAME", "Positions")

SPREADSHEET_ID = GOOGLE_SHEETS_SPREADSHEET_ID


def retry(exceptions, tries=3, delay=1.0, backoff=2.0):
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions:
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry
    return deco_retry


_lock = threading.Lock()


class SheetsService:
    def __init__(self):
        self._client = None
        self._spreadsheet = None
        self.SPREADSHEET_ID = SPREADSHEET_ID
        self._degraded = False

    def _init_client(self):
        if self._client and self._spreadsheet:
            return
        try:
            creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
            if not creds_json:
                raise Exception("GOOGLE_CREDENTIALS_JSON not set")
            try:
                info = json.loads(creds_json)
            except Exception:
                with open(creds_json, "r", encoding="utf-8") as fh:
                    info = json.load(fh)
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            credentials = Credentials.from_service_account_info(info, scopes=scopes)
            self._client = gspread.authorize(credentials)
            if not self.SPREADSHEET_ID:
                raise Exception("GOOGLE_SHEETS_SPREADSHEET_ID not set")
            self._spreadsheet = self._client.open_by_key(self.SPREADSHEET_ID)
        except Exception as e:
            print("⚠ Sheets init failed, entering degraded mode:", e)
            self._degraded = True
            self._client = None
            self._spreadsheet = None

    def _get_sheet(self, name: str):
        self._init_client()
        if not self._spreadsheet:
            return None
        try:
            return self._spreadsheet.worksheet(name)
        except Exception:
            return None

    @retry(Exception, tries=3, delay=1.0)
    def create_sheet_if_missing(self, name: str, headers: List[str]):
        with _lock:
            sh = self._get_sheet(name)
            if sh:
                return sh
            if not self._spreadsheet:
                raise Exception("Spreadsheet not available (degraded mode or init failed)")
            try:
                sh = self._spreadsheet.add_worksheet(
                    title=name,
                    rows="1000",
                    cols=str(max(20, len(headers))),
                )
                sh.append_row(headers)
                return sh
            except Exception:
                sh = self._get_sheet(name)
                if sh:
                    return sh
                raise

    @retry(Exception, tries=3, delay=1.0)
    def ensure_headers(self, sheet, headers: List[str]):
        with _lock:
            current = sheet.row_values(1)
            if not current:
                sheet.insert_row(headers, index=1)
                return
            missing = [h for h in headers if h not in current]
            if missing:
                sheet.resize(rows=sheet.row_count, cols=len(current) + len(missing))
                for h in missing:
                    current.append(h)
                sheet.update("1:1", [current])

    def smart_validate_sheets(self):
        users_headers = [
            "user_id",
            "username",
            "full_name_telegram",
            "role",
            "city",
            "email",
            "phone",
            "referrer",
            "joined_via_expert_id",
            "created_at",
        ]
        experts_headers = [
            "user_id",
            "expert_full_name",
            "expert_field",
            "expert_experience",
            "expert_position",
            "expert_links",
            "expert_why",
            "created_at",
            "status",
            "group_link",
            "supporters_count",
        ]
        positions_headers = [
            "position_id",
            "title",
            "description",
            "expert_user_id",
            "assigned_at",
        ]

        users_sheet = self.create_sheet_if_missing(USERS_SHEET_NAME, users_headers)
        experts_sheet = self.create_sheet_if_missing(EXPERTS_SHEET_NAME, experts_headers)
        positions_sheet = self.create_sheet_if_missing(POSITIONS_SHEET_NAME, positions_headers)

        self.ensure_headers(users_sheet, users_headers)
        self.ensure_headers(experts_sheet, experts_headers)
        self.ensure_headers(positions_sheet, positions_headers)

    def get_users_sheet(self):
        sh = self._get_sheet(USERS_SHEET_NAME)
        if not sh and not self._degraded:
            self.smart_validate_sheets()
            sh = self._get_sheet(USERS_SHEET_NAME)
        return sh

    def get_experts_sheet(self):
        sh = self._get_sheet(EXPERTS_SHEET_NAME)
        if not sh and not self._degraded:
            self.smart_validate_sheets()
            sh = self._get_sheet(EXPERTS_SHEET_NAME)
        return sh

    def get_positions_sheet(self):
        sh = self._get_sheet(POSITIONS_SHEET_NAME)
        if not sh and not self._degraded:
            self.smart_validate_sheets()
            sh = self._get_sheet(POSITIONS_SHEET_NAME)
        return sh

    def get_sheet_info(self, sheet):
        headers = sheet.row_values(1) or []
        rows = len(sheet.get_all_values()) - 1
        cols = len(headers)
        return {"headers": headers, "rows": rows, "cols": cols}

    # ========== Append / update ==========

    @retry(Exception, tries=3, delay=0.5)
    def append_user(self, user_record: Dict[str, Any]):
        sheet = self.get_users_sheet()
        if not sheet:
            raise Exception("Users sheet not available")
        headers = sheet.row_values(1)
        row = [user_record.get(h, "") for h in headers]
        with _lock:
            sheet.append_row(row)

    @retry(Exception, tries=3, delay=0.5)
    def append_expert(self, expert_record: Dict[str, Any]):
        sheet = self.get_experts_sheet()
        if not sheet:
            raise Exception("Experts sheet not available")
        headers = sheet.row_values(1)
        row = [expert_record.get(h, "") for h in headers]
        with _lock:
            sheet.append_row(row)

    @retry(Exception, tries=3, delay=0.5)
    def update_expert_status(self, user_id: str, status: str):
        sheet = self.get_experts_sheet()
        if not sheet:
            return False
        records = sheet.get_all_records()
        for idx, r in enumerate(records, start=2):
            if str(r.get("user_id")) == str(user_id):
                with _lock:
                    headers = sheet.row_values(1)
                    try:
                        col = headers.index("status") + 1
                    except ValueError:
                        headers.append("status")
                        sheet.update("1:1", [headers])
                        col = headers.index("status") + 1
                    sheet.update_cell(idx, col, status)
                return True
        return False

    # ========== Queries ==========

    def get_expert_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        sheet = self.get_experts_sheet()
        if not sheet:
            return None
        rows = sheet.get_all_records()
        for r in rows:
            if str(r.get("user_id")) == str(user_id):
                return r
        return None

    def get_supporter_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        sheet = self.get_users_sheet()
        if not sheet:
            return None
        rows = sheet.get_all_records()
        for r in rows:
            if str(r.get("user_id")) == str(user_id):
                return r
        return None

    @retry(Exception, tries=3, delay=0.5)
    def get_positions(self) -> List[Dict[str, Any]]:
        sheet = self.get_positions_sheet()
        if not sheet:
            return []
        return sheet.get_all_records()

    def get_position(self, position_id: str) -> Optional[Dict[str, Any]]:
        sheet = self.get_positions_sheet()
        if not sheet:
            return None
        rows = sheet.get_all_records()
        for r in rows:
            if str(r.get("position_id")) == str(position_id):
                return r
        return None

    def position_is_free(self, position_id: str) -> bool:
        pos = self.get_position(position_id)
        if not pos:
            return True
        return not bool(pos.get("expert_user_id"))

    # ========== Positions ==========

    @retry(Exception, tries=3, delay=0.5)
    def assign_position(self, position_id: str, user_id: str, timestamp: Optional[str] = None):
        sheet = self.get_positions_sheet()
        if not sheet:
            raise Exception("Positions sheet not available")
        rows = sheet.get_all_records()
        headers = sheet.row_values(1)
        for idx, r in enumerate(rows, start=2):
            if str(r.get("position_id")) == str(position_id):
                col_user = headers.index("expert_user_id") + 1 if "expert_user_id" in headers else None
                col_assigned = headers.index("assigned_at") + 1 if "assigned_at" in headers else None
                with _lock:
                    if col_user:
                        sheet.update_cell(idx, col_user, str(user_id))
                    if col_assigned:
                        sheet.update_cell(idx, col_assigned, timestamp or datetime.utcnow().isoformat())
                return True
        with _lock:
            row = [position_id] + [""] * (len(headers) - 1)
            sheet.append_row(row)
            self.assign_position(position_id, user_id, timestamp)
        return True

    @retry(Exception, tries=3, delay=0.5)
    def reset_position(self, position_id: str):
        sheet = self.get_positions_sheet()
        if not sheet:
            return False
        rows = sheet.get_all_records()
        headers = sheet.row_values(1)
        for idx, r in enumerate(rows, start=2):
            if str(r.get("position_id")) == str(position_id):
                with _lock:
                    if "expert_user_id" in headers:
                        sheet.update_cell(idx, headers.index("expert_user_id") + 1, "")
                    if "assigned_at" in headers:
                        sheet.update_cell(idx, headers.index("assigned_at") + 1, "")
                return True
        return False

    @retry(Exception, tries=3, delay=0.5)
    def reset_all_positions(self):
        sheet = self.get_positions_sheet()
        if not sheet:
            return False
        headers = sheet.row_values(1)
        rows = sheet.get_all_records()
        with _lock:
            for idx, _ in enumerate(rows, start=2):
                if "expert_user_id" in headers:
                    sheet.update_cell(idx, headers.index("expert_user_id") + 1, "")
                if "assigned_at" in headers:
                    sheet.update_cell(idx, headers.index("assigned_at") + 1, "")
        return True

    # ========== Duplicates / leaderboard ==========

    @retry(Exception, tries=3, delay=0.5)
    def clear_user_duplicates(self) -> int:
        sheet = self.get_users_sheet()
        if not sheet:
            return 0
        rows = sheet.get_all_records()
        seen = set()
        deleted = 0
        with _lock:
            for idx, r in reversed(list(enumerate(rows, start=2))):
                uid = str(r.get("user_id"))
                if uid in seen:
                    sheet.delete_rows(idx)
                    deleted += 1
                else:
                    seen.add(uid)
        return deleted

    @retry(Exception, tries=3, delay=0.5)
    def clear_expert_duplicates(self) -> int:
        sheet = self.get_experts_sheet()
        if not sheet:
            return 0
        rows = sheet.get_all_records()
        seen = set()
        deleted = 0
        with _lock:
            for idx, r in reversed(list(enumerate(rows, start=2))):
                uid = str(r.get("user_id"))
                if uid in seen:
                    sheet.delete_rows(idx)
                    deleted += 1
                else:
                    seen.add(uid)
        return deleted

    def get_experts_leaderboard(self) -> List[Dict[str, Any]]:
        sheet = self.get_experts_sheet()
        if not sheet:
            return []
        rows = sheet.get_all_records()

        def safe_int(x):
            try:
                return int(x)
            except Exception:
                return 0

        sorted_rows = sorted(
            rows,
            key=lambda r: safe_int(r.get("supporters_count", 0)),
            reverse=True,
        )
        return sorted_rows

    # ========== Helper/compat methods used ע"י flows/admin ==========

    def get_expert_status(self, user_id: str) -> Optional[str]:
        expert = self.get_expert_by_id(user_id)
        if not expert:
            return None
        return expert.get("status")

    def get_expert_position(self, user_id: str) -> Optional[str]:
        expert = self.get_expert_by_id(user_id)
        if not expert:
            return None
        return expert.get("expert_position")

    def get_expert_group_link(self, user_id: str) -> Optional[str]:
        expert = self.get_expert_by_id(user_id)
        if not expert:
            return None
        return expert.get("group_link")

    @retry(Exception, tries=3, delay=0.5)
    def increment_expert_supporters(self, user_id: str, step: int = 1):
        sheet = self.get_experts_sheet()
        if not sheet:
            return False
        rows = sheet.get_all_records()
        headers = sheet.row_values(1)
        try:
            col_idx = headers.index("supporters_count") + 1
        except ValueError:
            headers.append("supporters_count")
            sheet.update("1:1", [headers])
            col_idx = headers.index("supporters_count") + 1

        def safe_int(x):
            try:
                return int(x)
            except Exception:
                return 0

        with _lock:
            for idx, r in enumerate(rows, start=2):
                if str(r.get("user_id")) == str(user_id):
                    current = safe_int(r.get("supporters_count", 0))
                    sheet.update_cell(idx, col_idx, current + step)
                    return True
        return False

    def auto_fix_all_sheets(self):
        self.smart_validate_sheets()

    def validate_all_sheets(self):
        self.smart_validate_sheets()


sheets_service = SheetsService()

# ===============================
# Compatibility aliases ברמת המודול
# ===============================

def append_user(user_record: Dict[str, Any]):
    return sheets_service.append_user(user_record)

def append_expert(expert_record: Dict[str, Any]):
    return sheets_service.append_expert(expert_record)

def append_user_row(user_record: Dict[str, Any]):
    return sheets_service.append_user(user_record)

def append_expert_row(expert_record: Dict[str, Any]):
    return sheets_service.append_expert(expert_record)

def get_supporter_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    return sheets_service.get_supporter_by_id(user_id)

def get_expert_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    return sheets_service.get_expert_by_id(user_id)

def get_expert_status(user_id: str) -> Optional[str]:
    return sheets_service.get_expert_status(user_id)

def get_expert_position(user_id: str) -> Optional[str]:
    return sheets_service.get_expert_position(user_id)

def get_expert_group_link(user_id: str) -> Optional[str]:
    return sheets_service.get_expert_group_link(user_id)

def get_experts_leaderboard() -> List[Dict[str, Any]]:
    return sheets_service.get_experts_leaderboard()

def get_positions() -> List[Dict[str, Any]]:
    return sheets_service.get_positions()

def get_position(position_id: str) -> Optional[Dict[str, Any]]:
    return sheets_service.get_position(position_id)

def increment_expert_supporters(user_id: str, step: int = 1):
    return sheets_service.increment_expert_supporters(user_id, step=step)

def clear_user_duplicates() -> int:
    return sheets_service.clear_user_duplicates()

def clear_expert_duplicates() -> int:
    return sheets_service.clear_expert_duplicates()

def auto_fix_all_sheets():
    return sheets_service.auto_fix_all_sheets()

def validate_all_sheets():
    return sheets_service.validate_all_sheets()


__all__ = [
    "SPREADSHEET_ID",
    "sheets_service",
    "append_user",
    "append_expert",
    "append_user_row",
    "append_expert_row",
    "get_supporter_by_id",
    "get_expert_by_id",
    "get_expert_status",
    "get_expert_position",
    "get_expert_group_link",
    "get_experts_leaderboard",
    "get_positions",
    "get_position",
    "increment_expert_supporters",
    "clear_user_duplicates",
    "clear_expert_duplicates",
    "auto_fix_all_sheets",
    "validate_all_sheets",
    "smart_validate_sheets",
]
