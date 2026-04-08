from __future__ import annotations

from openai import OpenAI

from anderbot.config import settings
from anderbot.core.models import PluginMeta
from anderbot.core.plugin_base import BasePlugin


class Plugin(BasePlugin):
    meta = PluginMeta(
        name="ai_chat",
        version="0.1.0",
        description="基于 OpenAI SDK 的 AI 对话插件，可对接 iFlow 等兼容接口",
        commands=["/ai", "/clear"],
    )

    def __init__(self, manager):
        super().__init__(manager)
        self.client = OpenAI(base_url=settings.openai_base_url, api_key=settings.openai_api_key)

    async def handle_message(self, event):
        text = event.text
        if not text.startswith(settings.ai_trigger_prefix):
            return False

        prompt = text[len(settings.ai_trigger_prefix):].strip()
        if not prompt:
            await self.bot.reply(event, "用法：/ai 你的问题")
            return True

        session_key = f"group:{event.group_id}" if event.is_group else f"user:{event.user_id}"
        history = self.bot.sessions.get_messages(session_key)
        messages = [{"role": "system", "content": settings.ai_system_prompt}, *history, {"role": "user", "content": prompt}]

        try:
            completion = self.client.chat.completions.create(
                extra_body={},
                model=settings.openai_model,
                messages=messages,
            )
            answer = completion.choices[0].message.content or "(空响应)"
        except Exception as exc:
            self.logger.exception("ai completion failed")
            await self.bot.reply(event, f"AI 调用失败：{exc}")
            return True

        self.bot.sessions.append(session_key, "user", prompt)
        self.bot.sessions.append(session_key, "assistant", answer)
        await self.bot.reply(event, answer)
        return True
