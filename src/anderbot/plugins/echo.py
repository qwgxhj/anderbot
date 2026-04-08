from __future__ import annotations

from anderbot.core.models import PluginMeta
from anderbot.core.plugin_base import BasePlugin


class Plugin(BasePlugin):
    meta = PluginMeta(
        name="echo",
        version="0.1.0",
        description="基础回声、调试与事件观察",
        commands=["/echo"],
    )

    async def handle_message(self, event):
        if event.text.startswith("/echo "):
            await self.bot.reply(event, event.text[6:])
            return True
        return False
