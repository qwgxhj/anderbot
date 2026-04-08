from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import UTC, datetime
from typing import Any

import orjson
from fastapi import WebSocket


class ConsoleHub:
    def __init__(self, max_events: int = 200) -> None:
        self.logger = logging.getLogger("anderbot.console")
        self.clients: set[WebSocket] = set()
        self.events: deque[dict[str, Any]] = deque(maxlen=max_events)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.clients.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.clients.discard(websocket)

    def snapshot(self) -> list[dict[str, Any]]:
        return list(self.events)

    def client_count(self) -> int:
        return len(self.clients)

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        event = {
            "type": event_type,
            "time": datetime.now(UTC).isoformat(),
            "data": data,
        }
        self.events.append(event)
        if not self.clients:
            return
        message = orjson.dumps(event).decode()
        stale: list[WebSocket] = []
        for client in list(self.clients):
            try:
                await client.send_text(message)
            except Exception:
                stale.append(client)
        if stale:
            async with self._lock:
                for client in stale:
                    self.clients.discard(client)

    async def system_message(self, text: str, level: str = "info") -> None:
        await self.publish("system.message", {"level": level, "text": text})
