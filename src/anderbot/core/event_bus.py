from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any


EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        self._subscribers[topic].append(handler)

    async def publish(self, topic: str, data: dict[str, Any]) -> None:
        handlers = self._subscribers.get(topic, []) + self._subscribers.get("*", [])
        if not handlers:
            return
        await asyncio.gather(*(handler(data) for handler in handlers))
