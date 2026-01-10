# bot/core/monitoring.py
# מערכת ניטור ומטריקות פנימית פשוטה לשימוש בתוך הבוט
from datetime import datetime, timedelta
from typing import Dict, Any
from threading import Lock

from services import sheets_service

class Metrics:
    def __init__(self):
        self.total_users = 0
        self.messages_today = 0
        self.commands_today = {}
        self.errors = 0
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_users": self.total_users,
            "messages_today": self.messages_today,
            "commands_today": dict(self.commands_today),
            "errors": self.errors,
            "last_updated": self.last_updated.isoformat(),
        }

class Monitoring:
    def __init__(self):
        self.metrics = Metrics()
        self._users_seen = set()
        self._lock = Lock()
        self._daily_reset_at = datetime.utcnow().date()

    def track_message(self, user_id: int, kind: str = "message"):
        with self._lock:
            if user_id not in self._users_seen:
                self._users_seen.add(user_id)
                self.metrics.total_users += 1
            self.metrics.messages_today += 1
            self.metrics.last_updated = datetime.utcnow()

    def track_command(self, cmd: str):
        with self._lock:
            self.metrics.commands_today[cmd] = self.metrics.commands_today.get(cmd, 0) + 1
            self.metrics.last_updated = datetime.utcnow()

    def track_error(self, where: str, message: str = ""):
        with self._lock:
            self.metrics.errors += 1
            self.metrics.last_updated = datetime.utcnow()

    def update_metrics_from_sheets(self):
        """
        משיכה ראשונית של מדדים מתוך הגיליונות (כמו מספר תומכים/מומחים).
        זהו עדכון משלים ולא קריטי לפעולת הבוט.
        """
        try:
            users_sheet = sheets_service.get_users_sheet()
            experts_sheet = sheets_service.get_experts_sheet()
            users_count = len(users_sheet.get_all_records() or [])
            experts_count = len(experts_sheet.get_all_records() or [])
            with self._lock:
                # לא נשנה total_users כאן כי זה מדד מבוסס שימוש, אבל נשמור מידע עזר
                self.metrics.last_updated = datetime.utcnow()
                # ניתן להוסיף שדות נוספים אם נרצה
                self.metrics.extra = {
                    "users_count_sheet": users_count,
                    "experts_count_sheet": experts_count,
                }
        except Exception:
            # אל נפל — ניטור לא קריטי
            pass

    def cleanup_old_data(self, days_to_keep: int = 7):
        """
        ניקוי נתונים ישנים — כרגע אין אחסון היסטורי, אבל שומר מקום להרחבה.
        """
        # כרגע אין היסטוריה לשמור; שמור על API
        return

monitoring = Monitoring()
