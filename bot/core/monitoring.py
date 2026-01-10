# ===============================
# bot/core/monitoring.py – ניטור ומטריקות
# ===============================

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict

from services import sheets_service


@dataclass
class Metrics:
    total_users: int = 0
    messages_today: int = 0
    commands_today: Dict[str, int] = field(default_factory=dict)
    errors_today: Dict[str, int] = field(default_factory=dict)
    last_reset_date: date = field(default_factory=date.today)


class Monitoring:
    def __init__(self):
        self.metrics = Metrics()

    def _ensure_today(self):
        if self.metrics.last_reset_date != date.today():
            self.metrics = Metrics()

    def update_metrics_from_sheets(self):
        """קריאה חד־פעמית בעת עלייה – מעדכנת total_users מה־Sheets."""
        try:
            users_sheet = sheets_service.get_users_sheet()
            rows = users_sheet.get_all_records()
            self.metrics.total_users = len(rows)
        except Exception as e:
            print(f"⚠️ Failed to update metrics from sheets: {e}")

    def track_message(self, user_id: int, kind: str = "message"):
        """ניטור הודעות נכנסות (כל הודעה / כל callback)."""
        self._ensure_today()
        self.metrics.messages_today += 1

    def track_command(self, command_name: str):
        """ניטור פקודות /dashboard, /leaderboard וכו'."""
        self._ensure_today()
        self.metrics.commands_today[command_name] = (
            self.metrics.commands_today.get(command_name, 0) + 1
        )

    def track_error(self, source: str, message: str):
        """ניטור שגיאות לפי מקור (webhook_processing, sheets וכו')."""
        self._ensure_today()
        self.metrics.errors_today[source] = (
            self.metrics.errors_today.get(source, 0) + 1
        )
        print(f"❌ Error tracked from {source}: {message}")

    def cleanup_old_data(self, days_to_keep: int = 7):
        """כרגע שומר רק את היום – פונקציה לעתיד."""
        # אם נרצה היסטוריה – כאן נרחיב. כרגע לא נדרש.
        self._ensure_today()


monitoring = Monitoring()
