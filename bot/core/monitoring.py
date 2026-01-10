# bot/core/monitoring.py
# מערכת ניטור ומטריקות פנימית פשוטה לשימוש בתוך הבוט

from datetime import datetime
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
        self.extra = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_users": self.total_users,
            "messages_today": self.messages_today,
            "commands_today": dict(self.commands_today),
            "errors": self.errors,
            "last_updated": self.last_updated.isoformat(),
            "extra": self.extra,
        }


class Monitoring:
    def __init__(self):
        self.metrics = Metrics()
        self._users_seen = set()
        self._lock = Lock()

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
        try:
            users_sheet = sheets_service.get_users_sheet()
            experts_sheet = sheets_service.get_experts_sheet()
            users_count = len(users_sheet.get_all_records() or [])
            experts_count = len(experts_sheet.get_all_records() or [])
            with self._lock:
                self.metrics.extra = {
                    "users_count_sheet": users_count,
                    "experts_count_sheet": experts_count,
                }
                self.metrics.last_updated = datetime.utcnow()
        except Exception:
            pass

    def cleanup_old_data(self, days_to_keep: int = 7):
        return


monitoring = Monitoring()
