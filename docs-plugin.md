# 插件开发指南

## 插件接口

每个插件模块暴露一个 `Plugin` 类，并继承 `BasePlugin`。

```python
from anderbot.core.models import PluginMeta
from anderbot.core.plugin_base import BasePlugin

class Plugin(BasePlugin):
    meta = PluginMeta(
        name="demo",
        version="0.1.0",
        description="示例插件",
        commands=["/demo"],
    )

    async def handle_message(self, event):
        if event.text == "/demo":
            await self.bot.reply(event, "demo ok")
            return True
        return False
```

## 能力边界

插件可直接使用：

- `self.bot.reply(event, message)`
- `self.bot.send_group(group_id, message)`
- `self.bot.send_private(user_id, message)`
- `self.bot.sessions` 上下文会话
- `self.bot.store` JSON 运行时配置
- `self.bot.bus` 事件总线

## 推荐扩展方向

- 群管插件
- 签到/积分/经济系统
- RAG 知识库插件
- 多模型路由插件
- 图像生成插件
- Webhook 联动插件
- MCP / Tool Calling 插件
- 审核与风控插件
