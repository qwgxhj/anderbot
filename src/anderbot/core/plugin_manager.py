from __future__ import annotations

import importlib
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Type

from anderbot.core.plugin_base import BasePlugin


DEFAULT_PLUGINS = [
    "anderbot.plugins.help",
    "anderbot.plugins.echo",
    "anderbot.plugins.admin",
    "anderbot.plugins.ai_chat",
]


class PluginManager:
    def __init__(self, bot) -> None:
        self.bot = bot
        self.logger = logging.getLogger("anderbot.plugins")
        self.plugins: list[BasePlugin] = []

    def load_plugins(self, module_names: list[str] | None = None) -> None:
        names = module_names or self._load_from_config() or DEFAULT_PLUGINS
        for module_name in names:
            module = importlib.import_module(module_name)
            plugin_cls: Type[BasePlugin] = getattr(module, "Plugin")
            self.plugins.append(plugin_cls(self))
            self.logger.info("loaded plugin %s", module_name)

    def _load_from_config(self) -> list[str]:
        path = Path("config/plugins.json")
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return list(data.get("plugins", []))
        except Exception:
            self.logger.exception("failed to load plugin config")
            return []

    async def startup(self) -> None:
        for plugin in self.plugins:
            await plugin.startup()

    async def shutdown(self) -> None:
        for plugin in self.plugins:
            await plugin.shutdown()

    async def dispatch_message(self, event) -> bool:
        handled = False
        for plugin in self.plugins:
            if await plugin.handle_message(event):
                handled = True
                self.bot.stats.plugin_dispatches += 1
        return handled

    def snapshot(self) -> list[dict[str, object]]:
        return [asdict(plugin.meta) for plugin in self.plugins]
