from __future__ import annotations

import base64
import hmac
import json
import secrets
from hashlib import sha256
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Header, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse

from anderbot.bot import AnderBot
from anderbot.config import settings


CONSOLE_HTML = (Path(__file__).resolve().parent / "console.html").read_text(encoding="utf-8")
LOGIN_HTML = """
<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>AnderBot Login</title>
  <style>
    :root { color-scheme: dark; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; display: grid; place-items: center; font-family: Inter, Segoe UI, system-ui, sans-serif; background: #0b1020; color: #e5e7eb; }
    .card { width: min(420px, calc(100vw - 32px)); background: #111827; border: 1px solid #1f2937; border-radius: 16px; padding: 24px; }
    input, button { width: 100%; border-radius: 10px; border: 1px solid #334155; background: #0b1220; color: #e5e7eb; padding: 12px; font: inherit; margin-top: 10px; }
    button { background: #1d4ed8; border: none; cursor: pointer; }
    .muted { color: #94a3b8; font-size: 12px; }
    .err { color: #fca5a5; font-size: 13px; min-height: 18px; margin-top: 10px; }
  </style>
</head>
<body>
  <form class=\"card\" method=\"post\" action=\"/console/login\">
    <h1 style=\"margin-top:0;\">AnderBot Console</h1>
    <div class=\"muted\">输入 viewer / operator / admin 任一角色 token 登录。</div>
    <input name=\"token\" type=\"password\" placeholder=\"Console token\" autofocus />
    <input type=\"hidden\" name=\"next\" value=\"/console\" />
    <button type=\"submit\">登录</button>
    <div class=\"err\">__ERROR__</div>
  </form>
</body>
</html>
"""
ROLE_ORDER = {"viewer": 1, "operator": 2, "admin": 3}
COOKIE_NAME = "anderbot_console"


def _bearer_token(value: str | None) -> str:
    if not value:
        return ""
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return value.strip()


def _sign_session_payload(payload: str) -> str:
    digest = hmac.new(settings.console_session_secret.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()
    return f"{payload}.{digest}"


def _encode_session(role: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"role": role}).encode("utf-8")).decode("utf-8").rstrip("=")
    return _sign_session_payload(payload)


def _decode_session(token: str) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None
    payload, digest = token.rsplit(".", 1)
    expected = hmac.new(settings.console_session_secret.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()
    if not secrets.compare_digest(digest, expected):
        return None
    padding = "=" * (-len(payload) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode((payload + padding).encode("utf-8")).decode("utf-8"))
    except Exception:
        return None
    role = str(data.get("role", ""))
    if role not in ROLE_ORDER:
        return None
    return data


def _token_role(token: str) -> str | None:
    if not token:
        return None
    for role, role_token in settings.console_role_tokens.items():
        if secrets.compare_digest(token, role_token):
            return role
    return None


def _request_console_role(request: Request) -> str | None:
    bearer = _bearer_token(request.headers.get("authorization"))
    if bearer:
        return _token_role(bearer)
    session = _decode_session(request.cookies.get(COOKIE_NAME, ""))
    if session:
        return str(session["role"])
    query_token = request.query_params.get("token", "")
    return _token_role(query_token)


def _ws_console_role(websocket: WebSocket) -> str | None:
    token = websocket.query_params.get("token", "")
    role = _token_role(token)
    if role:
        return role
    cookie_header = websocket.headers.get("cookie", "")
    for chunk in cookie_header.split(";"):
        name, sep, value = chunk.strip().partition("=")
        if sep and name == COOKIE_NAME:
            session = _decode_session(value)
            if session:
                return str(session["role"])
    return None


def _require_console_role(request: Request, required_role: str = "viewer") -> str:
    role = _request_console_role(request)
    if not role or ROLE_ORDER[role] < ROLE_ORDER[required_role]:
        raise HTTPException(status_code=401 if not role else 403, detail=f"{required_role} role required")
    return role


def _require_ws_role(role: str | None, required_role: str = "viewer") -> None:
    if not role or ROLE_ORDER[role] < ROLE_ORDER[required_role]:
        raise HTTPException(status_code=401 if not role else 403, detail=f"{required_role} role required")


def _resolve_client_token(source: str, x_api_token: str | None, authorization: str | None) -> str:
    if x_api_token:
        return x_api_token.strip()
    bearer = _bearer_token(authorization)
    if bearer:
        return bearer
    mapping = settings.third_party_token_map
    return mapping.get(source, "")


def _check_webhook_auth(
    source: str,
    body_bytes: bytes,
    x_webhook_secret: str | None,
    x_webhook_signature_256: str | None,
    x_api_token: str | None,
    authorization: str | None,
) -> None:
    if settings.webhook_secret:
        secret_ok = x_webhook_secret and secrets.compare_digest(x_webhook_secret, settings.webhook_secret)
        if x_webhook_signature_256:
            expected = "sha256=" + hmac.new(settings.webhook_secret.encode("utf-8"), body_bytes, sha256).hexdigest()
            secret_ok = secret_ok or secrets.compare_digest(x_webhook_signature_256, expected)
        if not secret_ok:
            raise HTTPException(status_code=401, detail="invalid webhook signature or secret")

    token_map = settings.third_party_token_map
    if settings.webhook_token or token_map:
        provided = _resolve_client_token(source, x_api_token, authorization)
        expected = token_map.get(source) or settings.webhook_token
        if not provided or not expected or not secrets.compare_digest(provided, expected):
            raise HTTPException(status_code=401, detail="invalid webhook token")


def _render_console(role: str) -> str:
    return (
        CONSOLE_HTML.replace("__CONSOLE_TITLE__", settings.console_title)
        .replace("__CONSOLE_ROLE__", role)
    )


def create_app(bot: AnderBot) -> FastAPI:
    app = FastAPI(title="AnderBot API", version="0.1.0")

    @app.get("/")
    async def root():
        return {"name": "AnderBot", "status": "ok"}

    @app.get("/status")
    async def status(request: Request):
        role = _request_console_role(request)
        return bot.status_payload(console_role=role)

    @app.get("/console/login", response_class=HTMLResponse)
    async def console_login_page(error: str = ""):
        return LOGIN_HTML.replace("__ERROR__", error)

    @app.post("/console/login")
    async def console_login(token: str = Form(...), next: str = Form(default="/console")):
        role = _token_role(token.strip())
        if not role:
            return HTMLResponse(LOGIN_HTML.replace("__ERROR__", "Token 无效"), status_code=401)
        response = RedirectResponse(url=next or "/console", status_code=303)
        response.set_cookie(COOKIE_NAME, _encode_session(role), httponly=True, samesite="lax")
        return response

    @app.post("/console/logout")
    async def console_logout():
        response = RedirectResponse(url="/console/login", status_code=303)
        response.delete_cookie(COOKIE_NAME)
        return response

    @app.get("/console", response_class=HTMLResponse)
    async def console_page(request: Request):
        role = _request_console_role(request)
        if not role and settings.console_role_tokens:
            return RedirectResponse(url="/console/login", status_code=303)
        if not role:
            role = "admin"
        return _render_console(role)

    @app.websocket("/ws/console")
    async def console_ws(websocket: WebSocket):
        role = _ws_console_role(websocket)
        if settings.console_role_tokens and not role:
            await websocket.close(code=4401)
            return
        if not role:
            role = "admin"
        await bot.console.connect(websocket)
        try:
            await websocket.send_json({"type": "console.snapshot", "data": bot.console.snapshot()})
            await websocket.send_json({"type": "status.snapshot", "data": bot.status_payload(console_role=role)})
            await websocket.send_json({"type": "auth.role", "data": {"role": role}})
            while True:
                raw = await websocket.receive_json()
                action = str(raw.get("action", "")).strip()
                if action == "refresh_status":
                    await websocket.send_json({"type": "status.snapshot", "data": bot.status_payload(console_role=role)})
                elif action == "send_group_message":
                    _require_ws_role(role, "operator")
                    await bot.send_group(int(raw["group_id"]), raw.get("message", ""))
                    await websocket.send_json({"type": "action.ok", "data": {"action": action}})
                elif action == "send_private_message":
                    _require_ws_role(role, "operator")
                    await bot.send_private(int(raw["user_id"]), raw.get("message", ""))
                    await websocket.send_json({"type": "action.ok", "data": {"action": action}})
                elif action == "broadcast_system_message":
                    _require_ws_role(role, "admin")
                    await bot.console.system_message(str(raw.get("message", "")))
                    await websocket.send_json({"type": "action.ok", "data": {"action": action}})
                else:
                    await websocket.send_json({"type": "action.error", "data": {"detail": f"unknown action: {action}"}})
        except WebSocketDisconnect:
            pass
        except HTTPException as exc:
            await websocket.send_json({"type": "action.error", "data": {"detail": exc.detail}})
        finally:
            await bot.console.disconnect(websocket)

    @app.post("/send/group/{group_id}")
    async def send_group(group_id: int, body: dict[str, Any], request: Request):
        _require_console_role(request, "operator")
        await bot.send_group(group_id, body.get("message", ""))
        return {"ok": True}

    @app.post("/send/private/{user_id}")
    async def send_private(user_id: int, body: dict[str, Any], request: Request):
        _require_console_role(request, "operator")
        await bot.send_private(user_id, body.get("message", ""))
        return {"ok": True}

    @app.post("/webhooks/{source}")
    async def inbound_webhook(
        source: str,
        request: Request,
        x_webhook_secret: str | None = Header(default=None),
        x_webhook_signature_256: str | None = Header(default=None),
        x_api_token: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ):
        body_bytes = await request.body()
        try:
            _check_webhook_auth(source, body_bytes, x_webhook_secret, x_webhook_signature_256, x_api_token, authorization)
        except HTTPException:
            bot.stats.webhook_rejected += 1
            raise
        body = await request.json()
        return await bot.integration.handle_webhook_event(source, body)

    @app.get("/mcp")
    async def mcp_manifest():
        return bot.integration.mcp_manifest()

    @app.get("/mcp/tools")
    async def mcp_tools():
        return {"tools": bot.integration.mcp_manifest().get("tools", [])}

    @app.post("/mcp/call")
    async def mcp_call(body: dict[str, Any], request: Request, authorization: str | None = Header(default=None)):
        if settings.mcp_require_auth:
            role = _request_console_role(request) or _token_role(_bearer_token(authorization))
            if not role or ROLE_ORDER[role] < ROLE_ORDER["operator"]:
                raise HTTPException(status_code=401, detail="mcp auth required")
        tool_name = str(body.get("tool") or body.get("name") or "")
        arguments = body.get("arguments") or body.get("input") or {}
        if not tool_name:
            raise HTTPException(status_code=400, detail="tool is required")
        try:
            result = await bot.integration.mcp_call(tool_name, arguments)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": {
                "content": [
                    {
                        "type": "json",
                        "json": result,
                    }
                ],
                "structuredContent": result,
                "isError": False,
            },
        }

    return app
