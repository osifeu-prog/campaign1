# services/level_service.py
# ===============================
# ניהול נקודות, רמות ואימות משתמשים (תומכים + מומחים)
# ===============================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any

from services.sheets_service import sheets_service

UserRole = Literal["supporter", "expert"]


@dataclass
class LevelConfig:
    level: int
    min_points: int
    name: str


# הגדרת רמות בסיסית – ניתן לשנות בהמשך
LEVELS = [
    LevelConfig(level=0, min_points=0, name="משתמש חדש"),
    LevelConfig(level=1, min_points=10, name="פעיל"),
    LevelConfig(level=2, min_points=30, name="מוביל"),
    LevelConfig(level=3, min_points=50, name="מועמד מומחה"),
    LevelConfig(level=4, min_points=100, name="מומחה מאושר"),
]


class LevelService:
    def __init__(self):
        # שם העמודות שנוסיף בגיליונות
        self.points_field = "points"
        self.level_field = "level"
        self.verified_field = "verified"
        self.referrals_field = "referrals_count"

    # ===============================
    # עזר פנימי – הבטחת עמודות
    # ===============================

    def _ensure_user_fields(self):
        sheet = sheets_service.get_users_sheet()
        if not sheet:
            return
        headers = sheet.row_values(1) or []
        changed = False
        for field in [self.points_field, self.level_field, self.verified_field, self.referrals_field]:
            if field not in headers:
                headers.append(field)
                changed = True
        if changed:
            sheet.update("1:1", [headers])

    def _ensure_expert_fields(self):
        sheet = sheets_service.get_experts_sheet()
        if not sheet:
            return
        headers = sheet.row_values(1) or []
        changed = False
        for field in [self.points_field, self.level_field, self.verified_field, self.referrals_field]:
            if field not in headers:
                headers.append(field)
                changed = True
        if changed:
            sheet.update("1:1", [headers])

    # ===============================
    # עזר – המרת נקודות לרמה
    # ===============================

    def _level_for_points(self, points: int) -> LevelConfig:
        current = LEVELS[0]
        for cfg in LEVELS:
            if points >= cfg.min_points:
                current = cfg
        return current

    # ===============================
    # קריאה/עדכון נתוני משתמש/מומחה
    # ===============================

    def _get_record(
        self, user_id: int, role: UserRole
    ) -> tuple[Optional[Dict[str, Any]], Optional[int], Optional[Any]]:
        """
        מחזיר (רשומה, אינדקס שורה, sheet) לפי user_id ותפקיד.
        """
        if role == "supporter":
            sheet = sheets_service.get_users_sheet()
        else:
            sheet = sheets_service.get_experts_sheet()

        if not sheet:
            return None, None, None

        rows = sheet.get_all_records()
        for idx, row in enumerate(rows, start=2):
            if str(row.get("user_id")) == str(user_id):
                return row, idx, sheet
        return None, None, sheet

    def get_points(self, user_id: int, role: UserRole) -> int:
        record, _, _ = self._get_record(user_id, role)
        if not record:
            return 0
        try:
            return int(record.get(self.points_field, 0))
        except Exception:
            return 0

    def get_level(self, user_id: int, role: UserRole) -> int:
        record, _, _ = self._get_record(user_id, role)
        if not record:
            return 0
        try:
            return int(record.get(self.level_field, 0))
        except Exception:
            return 0

    def get_level_name(self, user_id: int, role: UserRole) -> str:
        points = self.get_points(user_id, role)
        cfg = self._level_for_points(points)
        return cfg.name

    def is_verified(self, user_id: int, role: UserRole) -> bool:
        record, _, _ = self._get_record(user_id, role)
        if not record:
            return False
        v = record.get(self.verified_field, "")
        return str(v).strip().lower() in ("1", "true", "yes", "y")

    def mark_verified(self, user_id: int, role: UserRole, value: bool = True) -> bool:
        record, row_idx, sheet = self._get_record(user_id, role)
        if not sheet or row_idx is None:
            return False

        if role == "supporter":
            self._ensure_user_fields()
        else:
            self._ensure_expert_fields()

        headers = sheet.row_values(1) or []
        if self.verified_field not in headers:
            headers.append(self.verified_field)
            sheet.update("1:1", [headers])
        col_idx = headers.index(self.verified_field) + 1
        sheet.update_cell(row_idx, col_idx, "1" if value else "0")
        return True

    # ===============================
    # עדכון נקודות + רמה
    # ===============================

    def add_points(self, user_id: int, role: UserRole, amount: int) -> int:
        """
        מוסיף נקודות למשתמש ומעדכן רמה. מחזיר את סך הנקודות החדש.
        """
        record, row_idx, sheet = self._get_record(user_id, role)
        if not sheet or row_idx is None:
            return 0

        if role == "supporter":
            self._ensure_user_fields()
        else:
            self._ensure_expert_fields()

        headers = sheet.row_values(1) or []
        # points column
        if self.points_field not in headers:
            headers.append(self.points_field)
            sheet.update("1:1", [headers])
        points_col = headers.index(self.points_field) + 1

        # level column
        if self.level_field not in headers:
            headers.append(self.level_field)
            sheet.update("1:1", [headers])
        level_col = headers.index(self.level_field) + 1

        # current points
        try:
            current_points = int(record.get(self.points_field, 0))
        except Exception:
            current_points = 0

        new_points = max(0, current_points + amount)
        cfg = self._level_for_points(new_points)
        with sheets_service._lock:  # משתמשים באותו lock גלובלי של sheets_service
            sheet.update_cell(row_idx, points_col, new_points)
            sheet.update_cell(row_idx, level_col, cfg.level)

        return new_points

    def get_next_level_info(self, user_id: int, role: UserRole) -> Optional[Dict[str, Any]]:
        points = self.get_points(user_id, role)
        current_cfg = self._level_for_points(points)
        # למצוא את הרמה הבאה
        next_cfg: Optional[LevelConfig] = None
        for cfg in LEVELS:
            if cfg.min_points > current_cfg.min_points:
                if not next_cfg or cfg.min_points < next_cfg.min_points:
                    next_cfg = cfg
        if not next_cfg:
            return None
        missing = max(0, next_cfg.min_points - points)
        return {
            "current_level": current_cfg.level,
            "current_name": current_cfg.name,
            "current_points": points,
            "next_level": next_cfg.level,
            "next_name": next_cfg.name,
            "required_points": next_cfg.min_points,
            "missing_points": missing,
        }


level_service = LevelService()
