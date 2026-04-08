from __future__ import annotations

from dataclasses import asdict
from typing import Any


class IntegrationService:
    def __init__(self, bot) -> None:
        self.bot = bot

    async def handle_webhook_event(self, source: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.bot.stats.inbound_webhooks += 1
        await self.bot.console.publish(
            "webhook.received",
            {
                "source": source,
                "payload": payload,
            },
        )
        return {
            "accepted": True,
            "source": source,
            "echo": payload,
        }

    def mcp_manifest(self) -> dict[str, Any]:
        tools = [
            {
                "name": "status",
                "description": "Get AnderBot runtime status",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "send_group_message",
                "description": "Send a group message through NapCat",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "group_id": {"type": "integer"},
                        "message": {"type": "string"},
                    },
                    "required": ["group_id", "message"],
                },
            },
            {
                "name": "send_private_message",
                "description": "Send a private message through NapCat",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer"},
                        "message": {"type": "string"},
                    },
                    "required": ["user_id", "message"],
                },
            },
            {
                "name": "plugins",
                "description": "List loaded plugins",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]
        return {
            "name": self.bot.settings.mcp_server_name,
            "version": self.bot.settings.mcp_server_version,
            "protocolVersion": "2025-03-26",
            "protocol": "mcp-http-draft",
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {},
                "prompts": {},
            },
            "serverInfo": {
                "name": self.bot.settings.mcp_server_name,
                "version": self.bot.settings.mcp_server_version,
            },
            "tools": tools,
        }

    async def mcp_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.bot.stats.mcp_calls += 1
        await self.bot.console.publish("mcp.call", {"tool": tool_name, "arguments": arguments})
        if tool_name == "status":
            return self.bot.status_payload()
        if tool_name == "plugins":
            return {"plugins": self.bot.plugins.snapshot()}
        if tool_name == "send_group_message":
            await self.bot.send_group(int(arguments["group_id"]), str(arguments["message"]))
            return {"ok": True}
        if tool_name == "send_private_message":
            await self.bot.send_private(int(arguments["user_id"]), str(arguments["message"]))
            return {"ok": True}
        raise ValueError(f"unknown MCP tool: {tool_name}")
