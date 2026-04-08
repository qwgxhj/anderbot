from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from anderbot.core.models import MessageEvent, PluginMeta

if TYPE_CHECKING:
    from anderbot.core.plugin_manager import PluginManager


class BasePlugin(ABC):
    meta = PluginMeta(name="base", version="0.0.0", description="base plugin")

    def __init__(self, manager: "PluginManager") -> None:
        self.manager = manager
        self.bot = manager.bot
        self.logger = logging.getLogger(f"anderbot.plugin.{self.meta.name}")

    async def startup(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    @abstractmethod
    async def handle_message(self, event: MessageEvent) -> bool:
        raise NotImplementedError
