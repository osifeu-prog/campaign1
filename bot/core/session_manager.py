# bot/core/session_manager.py
# ניהול סשנים ו־State Machine בסיסי

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from telegram import User


@dataclass
class UserSession:
    user_id: int
    username: str
    full_name: str
    created_at: str
    last_flow: Optional[str] = None
    last_state: Optional[str] = None
    last_message_id: Optional[int] = None
    last_deeplink: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "full_name": self.full_name,
            "created_at": self.created_at,
            "last_flow": self.last_flow,
            "last_state": self.last_state,
            "last_message_id": self.last_message_id,
            "last_deeplink": self.last_deeplink,
            "metadata": self.metadata,
        }


class SessionManager:
    def __init__(self):
        self._sessions: Dict[int, UserSession] = {}

    def get_or_create(self, user: User, start_param: Optional[str] = None) -> UserSession:
        if user.id in self._sessions:
            session = self._sessions[user.id]
        else:
            session = UserSession(
                user_id=user.id,
                username=user.username or "",
                full_name=user.full_name,
                created_at=datetime.utcnow().isoformat(),
            )
            self._sessions[user.id] = session

        if start_param:
            session.last_deeplink = start_param

        return session

    def update_state(
        self,
        user_id: int,
        flow: Optional[str] = None,
        state: Optional[str] = None,
        message_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        session = self._sessions.get(user_id)
        if not session:
            return

        if flow is not None:
            session.last_flow = flow
        if state is not None:
            session.last_state = state
        if message_id is not None:
            session.last_message_id = message_id
        if metadata:
            session.metadata.update(metadata)

    def get_session(self, user_id: int) -> Optional[UserSession]:
        return self._sessions.get(user_id)

    def clear_flow(self, user_id: int):
        session = self._sessions.get(user_id)
        if not session:
            return
        session.last_flow = None
        session.last_state = None
        session.last_message_id = None


session_manager = SessionManager()
