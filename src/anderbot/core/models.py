from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MessageEvent:
    post_type: str
    message_type: str
    user_id: int
    group_id: int | None
    raw_message: str
    message_id: int | None
    sender: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    message_segments: list[dict[str, Any]] = field(default_factory=list)
    cq_message: str = ""

    @property
    def is_private(self) -> bool:
        return self.message_type == "private"

    @property
    def is_group(self) -> bool:
        return self.message_type == "group"

    @property
    def text(self) -> str:
        return self.raw_message.strip()


@dataclass(slots=True)
class PluginMeta:
    name: str
    version: str
    description: str
    commands: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BotStats:
    received_events: int = 0
    sent_messages: int = 0
    plugin_dispatches: int = 0
    inbound_webhooks: int = 0
    console_clients: int = 0
    napcat_reconnects: int = 0
    napcat_send_failures: int = 0
    webhook_rejected: int = 0
    mcp_calls: int = 0
