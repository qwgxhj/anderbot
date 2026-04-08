from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from anderbot.adapters.napcat import NapCatAdapter
from anderbot.config import settings
from anderbot.core.event_bus import EventBus
from anderbot.core.models import BotStats, MessageEvent
from anderbot.core.plugin_manager import PluginManager
from anderbot.core.session import SessionManager
from anderbot.core.store import JsonStore
from anderbot.integrations.service import IntegrationService
from anderbot.web.console import ConsoleHub


class AnderBot:
    def __init__(self) -> None:
        self.logger = logging.getLogger("anderbot")
        self.settings = settings
        self.stats = BotStats()
        self.bus = EventBus()
        self.sessions = SessionManager()
        self.store = JsonStore(Path("config/runtime.json"))
        self.console = ConsoleHub()
        self.integration = IntegrationService(self)
        self.adapter = NapCatAdapter(self, settings.napcat_ws_url, settings.napcat_token)
        self.plugins = PluginManager(self)
        self.plugins.load_plugins()

    async def startup(self) -> None:
        await self.plugins.startup()
        await self.console.publish("system.started", self.status_payload())
        self.logger.info("%s started", settings.app_name)

    async def shutdown(self) -> None:
        await self.adapter.close()
        await self.plugins.shutdown()

    async def serve_forever(self) -> None:
        await self.startup()
        await self.adapter.recv_loop()

    def status_payload(self, console_role: str | None = None) -> dict[str, Any]:
        self.stats.console_clients = self.console.client_count()
        return {
            "app": {
                "name": self.settings.app_name,
                "env": self.settings.app_env,
                "host": self.settings.anderbot_host,
                "port": self.settings.anderbot_port,
                "napcat_ws_url": self.settings.napcat_ws_url,
            },
            "stats": asdict(self.stats),
            "plugins": self.plugins.snapshot(),
            "auth": {
                "console_role": console_role,
                "roles_enabled": sorted(self.settings.console_role_tokens.keys()),
            },
        }

    async def handle_payload(self, payload: dict) -> None:
        self.stats.received_events += 1
        await self.console.publish("napcat.payload", payload)
        await self.bus.publish(payload.get("post_type", "unknown"), payload)
        event = self.adapter.parse_event(payload)
        if event is None:
            return
        if not self._is_allowed(event):
            await self.console.publish("message.blocked", {"reason": "group_not_whitelisted", "event": event.payload})
            return
        await self.console.publish(
            "message.received",
            {
                "user_id": event.user_id,
                "group_id": event.group_id,
                "message": event.raw_message,
                "message_type": event.message_type,
                "cq_message": event.cq_message,
                "segments": event.message_segments,
            },
        )
        await self.plugins.dispatch_message(event)

    def _is_allowed(self, event: MessageEvent) -> bool:
        if event.is_group and settings.whitelisted_groups and event.group_id not in settings.whitelisted_groups:
            return False
        return True

    async def reply(self, event: MessageEvent, message: str | list[Any]) -> None:
        await self.adapter.send_text(user_id=event.user_id if event.is_private else None, group_id=event.group_id, message=message)
        self.stats.sent_messages += 1
        await self.console.publish(
            "message.sent",
            {
                "target": "reply",
                "message": message,
                "group_id": event.group_id,
                "user_id": event.user_id,
            },
        )

    async def send_private(self, user_id: int, message: str | list[Any]) -> None:
        await self.adapter.send_text(user_id=user_id, message=message)
        self.stats.sent_messages += 1
        await self.console.publish("message.sent", {"target": "private", "user_id": user_id, "message": message})

    async def send_group(self, group_id: int, message: str | list[Any]) -> None:
        await self.adapter.send_text(group_id=group_id, message=message)
        self.stats.sent_messages += 1
        await self.console.publish("message.sent", {"target": "group", "group_id": group_id, "message": message})
