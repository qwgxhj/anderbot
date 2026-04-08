from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import orjson
import websockets
from websockets.exceptions import ConnectionClosed

from anderbot.core.models import MessageEvent


_CQ_ESCAPE_ENCODE = {
    "&": "&amp;",
    "[": "&#91;",
    "]": "&#93;",
    ",": "&#44;",
}
_CQ_ESCAPE_DECODE = {v: k for k, v in _CQ_ESCAPE_ENCODE.items()}
_CQ_RE = re.compile(r"\[CQ:(?P<type>[^,\]]+)(?:,(?P<data>[^\]]*))?\]")


class NapCatAdapter:
    def __init__(self, bot, ws_url: str, token: str = "") -> None:
        self.bot = bot
        self.ws_url = ws_url
        self.token = token
        self.logger = logging.getLogger("anderbot.napcat")
        self.ws = None

    async def connect(self) -> None:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else None
        self.ws = await websockets.connect(self.ws_url, additional_headers=headers)
        self.logger.info("connected to napcat %s", self.ws_url)
        await self.bot.console.publish("napcat.connected", {"ws_url": self.ws_url})

    async def close(self) -> None:
        if self.ws is not None:
            await self.ws.close()
            self.ws = None

    async def ensure_connected(self) -> None:
        if self.ws is None or getattr(self.ws, "closed", False):
            await self.connect()

    async def recv_loop(self) -> None:
        backoff = max(0.5, self.bot.settings.napcat_reconnect_base_seconds)
        backoff_max = max(backoff, self.bot.settings.napcat_reconnect_max_seconds)
        while True:
            try:
                await self.ensure_connected()
                assert self.ws is not None
                async for raw in self.ws:
                    payload = orjson.loads(raw)
                    await self.bot.handle_payload(payload)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.bot.stats.napcat_reconnects += 1
                self.logger.warning("napcat connection lost: %s", exc)
                await self.bot.console.publish(
                    "napcat.disconnected",
                    {
                        "ws_url": self.ws_url,
                        "error": repr(exc),
                        "retry_in_seconds": backoff,
                    },
                )
                await self.close()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, backoff_max)

    async def call_api(self, action: str, params: dict[str, Any]) -> None:
        try:
            await self.ensure_connected()
            assert self.ws is not None
            await self.ws.send(orjson.dumps({"action": action, "params": params}).decode())
        except Exception:
            self.bot.stats.napcat_send_failures += 1
            await self.close()
            raise

    async def send_text(self, *, user_id: int | None = None, group_id: int | None = None, message: str | list[Any]) -> None:
        normalized = self.normalize_message_out(message)
        if group_id is not None:
            await self.call_api("send_group_msg", {"group_id": group_id, "message": normalized})
        elif user_id is not None:
            await self.call_api("send_private_msg", {"user_id": user_id, "message": normalized})
        else:
            raise ValueError("user_id or group_id required")

    def parse_event(self, payload: dict[str, Any]) -> MessageEvent | None:
        if payload.get("post_type") != "message":
            return None
        segments = self.normalize_message_in(payload.get("message"), payload.get("raw_message", ""))
        raw_message = payload.get("raw_message") or self.segments_to_text(segments)
        return MessageEvent(
            post_type=payload.get("post_type", ""),
            message_type=payload.get("message_type", ""),
            user_id=int(payload.get("user_id", 0)),
            group_id=int(payload["group_id"]) if payload.get("group_id") else None,
            raw_message=raw_message,
            message_id=payload.get("message_id"),
            sender=payload.get("sender", {}),
            payload=payload,
            message_segments=segments,
            cq_message=self.segments_to_cq(segments),
        )

    def normalize_message_in(self, message: Any, raw_message: str) -> list[dict[str, Any]]:
        if isinstance(message, list):
            return [self._segment_object(item) for item in message]
        if isinstance(message, str) and "[CQ:" in message:
            return self.cq_to_segments(message)
        if raw_message and "[CQ:" in raw_message:
            return self.cq_to_segments(raw_message)
        text = raw_message if raw_message else (message if isinstance(message, str) else "")
        return [{"type": "text", "data": {"text": text}}] if text else []

    def normalize_message_out(self, message: str | list[Any]) -> list[dict[str, Any]] | str:
        if isinstance(message, list):
            return [self._segment_object(item) for item in message]
        if isinstance(message, str) and "[CQ:" in message:
            return self.cq_to_segments(message)
        return message

    def segments_to_text(self, segments: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for segment in segments:
            seg_type = segment.get("type")
            data = segment.get("data", {}) or {}
            if seg_type == "text":
                parts.append(str(data.get("text", "")))
            elif seg_type == "at":
                qq = data.get("qq") or data.get("user_id") or ""
                parts.append(f"@{qq}")
            elif seg_type == "image":
                parts.append("[图片]")
            elif seg_type == "face":
                parts.append("[表情]")
            elif seg_type == "reply":
                parts.append("[回复]")
            else:
                parts.append(f"[{seg_type}]")
        return "".join(parts)

    def segments_to_cq(self, segments: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for segment in segments:
            seg_type = str(segment.get("type", "text"))
            data = segment.get("data", {}) or {}
            if seg_type == "text":
                parts.append(self._escape_cq_text(str(data.get("text", ""))))
                continue
            if data:
                params = ",".join(f"{key}={self._escape_cq_text(str(value))}" for key, value in data.items())
                parts.append(f"[CQ:{seg_type},{params}]")
            else:
                parts.append(f"[CQ:{seg_type}]")
        return "".join(parts)

    def cq_to_segments(self, text: str) -> list[dict[str, Any]]:
        segments: list[dict[str, Any]] = []
        last_index = 0
        for match in _CQ_RE.finditer(text):
            if match.start() > last_index:
                prefix = text[last_index:match.start()]
                if prefix:
                    segments.append({"type": "text", "data": {"text": self._unescape_cq_text(prefix)}})
            seg_type = self._unescape_cq_text(match.group("type"))
            raw_data = match.group("data") or ""
            data: dict[str, Any] = {}
            if raw_data:
                for item in raw_data.split(","):
                    if "=" not in item:
                        continue
                    key, value = item.split("=", 1)
                    data[self._unescape_cq_text(key)] = self._unescape_cq_text(value)
            segments.append({"type": seg_type, "data": data})
            last_index = match.end()
        if last_index < len(text):
            suffix = text[last_index:]
            if suffix:
                segments.append({"type": "text", "data": {"text": self._unescape_cq_text(suffix)}})
        return segments

    def _segment_object(self, item: Any) -> dict[str, Any]:
        if isinstance(item, dict):
            return {
                "type": str(item.get("type", "text")),
                "data": dict(item.get("data", {}) or {}),
            }
        return {"type": "text", "data": {"text": str(item)}}

    def _escape_cq_text(self, value: str) -> str:
        for raw, escaped in _CQ_ESCAPE_ENCODE.items():
            value = value.replace(raw, escaped)
        return value

    def _unescape_cq_text(self, value: str) -> str:
        for escaped, raw in _CQ_ESCAPE_DECODE.items():
            value = value.replace(escaped, raw)
        return value
