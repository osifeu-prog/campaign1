# ===============================
# rate_limiter – הגבלת תדירות פעולות למשתמש
# ===============================

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple


class RateLimiter:
    def __init__(self):
        self._counters: Dict[Tuple[int, str], Tuple[int, datetime]] = defaultdict(
            lambda: (0, datetime.utcnow())
        )

    def allow(self, user_id: int, event_key: str, limit: int, per_seconds: int) -> bool:
        now = datetime.utcnow()
        key = (user_id, event_key)
        count, window_start = self._counters[key]

        if now - window_start > timedelta(seconds=per_seconds):
            self._counters[key] = (1, now)
            return True

        if count < limit:
            self._counters[key] = (count + 1, window_start)
            return True

        return False


rate_limiter = RateLimiter()
