from __future__ import annotations

from anderbot.config import settings
from anderbot.core.models import PluginMeta
from anderbot.core.plugin_base import BasePlugin


class Plugin(BasePlugin):
    meta = PluginMeta(
        name="admin",
        version="0.1.0",
        description="基础管理能力：群开关、清理上下文",
        commands=["/clear", "/enable", "/disable"],
    )

    async def handle_message(self, event):
        text = event.text
        session_key = f"group:{event.group_id}" if event.is_group else f"user:{event.user_id}"

        if text == "/clear":
            self.bot.sessions.clear(session_key)
            await self.bot.reply(event, "上下文已清空。")
            return True

        if event.user_id not in settings.superuser_ids:
            return False

        if text.startswith("/enable group "):
            group_id = int(text.split()[-1])
            data = self.bot.store.read()
            groups = set(data.get("enabled_groups", []))
            groups.add(group_id)
            data["enabled_groups"] = sorted(groups)
            self.bot.store.write(data)
            await self.bot.reply(event, f"已启用群 {group_id}")
            return True

        if text.startswith("/disable group "):
            group_id = int(text.split()[-1])
            data = self.bot.store.read()
            groups = set(data.get("enabled_groups", []))
            groups.discard(group_id)
            data["enabled_groups"] = sorted(groups)
            self.bot.store.write(data)
            await self.bot.reply(event, f"已禁用群 {group_id}")
            return True

        return False
