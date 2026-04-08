from __future__ import annotations

from anderbot.core.models import PluginMeta
from anderbot.core.plugin_base import BasePlugin


class Plugin(BasePlugin):
    meta = PluginMeta(
        name="help",
        version="0.1.0",
        description="命令帮助与插件清单",
        commands=["/help", "/plugins", "/status"],
    )

    async def handle_message(self, event):
        text = event.text
        if text == "/help":
            await self.bot.reply(event, "可用命令：/help /plugins /status /echo /ai /clear /enable /disable")
            return True
        if text == "/plugins":
            plugins = self.manager.snapshot()
            lines = [f"- {p['name']} {p['version']}: {p['description']}" for p in plugins]
            await self.bot.reply(event, "已加载插件：\n" + "\n".join(lines))
            return True
        if text == "/status":
            s = self.bot.stats
            await self.bot.reply(event, f"AnderBot 运行中\nreceived={s.received_events}\nsent={s.sent_messages}\ndispatch={s.plugin_dispatches}")
            return True
        return False
