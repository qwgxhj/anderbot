from __future__ import annotations

import logging
from collections import defaultdict, deque


class SessionManager:
    def __init__(self, max_turns: int = 12) -> None:
        self._sessions = defaultdict(lambda: deque(maxlen=max_turns * 2))
        self.logger = logging.getLogger("anderbot.session")

    def append(self, key: str, role: str, content: str) -> None:
        self._sessions[key].append({"role": role, "content": content})

    def get_messages(self, key: str) -> list[dict[str, str]]:
        return list(self._sessions[key])

    def clear(self, key: str) -> None:
        self._sessions.pop(key, None)
