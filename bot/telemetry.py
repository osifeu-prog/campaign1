# ===============================
# telemetry – Analytics + A/B Testing Hooks
# ===============================

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Literal, Optional

from telegram import User
from telegram.ext import ContextTypes

from services.logger_service import log


Variant = Literal["A", "B"]


@dataclass
class ABTestAssignment:
    experiment: str
    variant: Variant


class Telemetry:
    """
    אחראי על:
    - תיעוד אירועים (analytics)
    - שיוך משתמשים ל־A/B variants
    """

    def __init__(self):
        # experiment_name -> dict(user_id -> variant)
        self._experiments: Dict[str, Dict[int, Variant]] = {}

    def get_variant(self, experiment: str, user: User) -> Variant:
        if experiment not in self._experiments:
            self._experiments[experiment] = {}

        exp_map = self._experiments[experiment]
        if user.id in exp_map:
            return exp_map[user.id]

        # hash-based deterministic assignment
        h = hashlib.sha256(f"{experiment}:{user.id}".encode()).hexdigest()
        variant: Variant = "A" if int(h, 16) % 2 == 0 else "B"
        exp_map[user.id] = variant
        return variant

    async def track_event(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        event_name: str,
        user: Optional[User] = None,
        properties: Optional[Dict[str, Any]] = None,
    ):
        props = properties.copy() if properties else {}
        props["event_name"] = event_name
        props["timestamp"] = datetime.utcnow().isoformat()
        await log(
            context,
            f"Telemetry event: {event_name}",
            user=user,
            extra=props,
        )


telemetry = Telemetry()
