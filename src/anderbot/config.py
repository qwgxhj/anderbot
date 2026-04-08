from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AnderBot"
    app_env: str = Field(default="dev", alias="APP_ENV")
    napcat_ws_url: str = Field(default="ws://127.0.0.1:3001", alias="NAPCAT_WS_URL")
    napcat_token: str = Field(default="", alias="NAPCAT_TOKEN")
    napcat_reconnect_base_seconds: float = Field(default=2.0, alias="NAPCAT_RECONNECT_BASE_SECONDS")
    napcat_reconnect_max_seconds: float = Field(default=30.0, alias="NAPCAT_RECONNECT_MAX_SECONDS")
    anderbot_host: str = Field(default="0.0.0.0", alias="ANDERBOT_HOST")
    anderbot_port: int = Field(default=8099, alias="ANDERBOT_PORT")
    superusers: str = Field(default="", alias="SUPERUSERS")
    group_whitelist: str = Field(default="", alias="GROUP_WHITELIST")
    openai_base_url: str = Field(default="https://apis.iflow.cn/v1", alias="OPENAI_BASE_URL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="TBStars2-200B-A13B", alias="OPENAI_MODEL")
    ai_trigger_prefix: str = Field(default="/ai", alias="AI_TRIGGER_PREFIX")
    ai_system_prompt: str = Field(default="你是 AnderBot 的开放生态 AI 助手。", alias="AI_SYSTEM_PROMPT")
    console_title: str = Field(default="AnderBot Console", alias="CONSOLE_TITLE")
    console_token: str = Field(default="", alias="CONSOLE_TOKEN")
    console_viewer_token: str = Field(default="", alias="CONSOLE_VIEWER_TOKEN")
    console_operator_token: str = Field(default="", alias="CONSOLE_OPERATOR_TOKEN")
    console_admin_token: str = Field(default="", alias="CONSOLE_ADMIN_TOKEN")
    console_session_secret: str = Field(default="change-me-session-secret", alias="CONSOLE_SESSION_SECRET")
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")
    webhook_token: str = Field(default="", alias="WEBHOOK_TOKEN")
    third_party_tokens: str = Field(default="", alias="THIRD_PARTY_TOKENS")
    mcp_server_name: str = Field(default="anderbot-mcp", alias="MCP_SERVER_NAME")
    mcp_server_version: str = Field(default="0.1.0", alias="MCP_SERVER_VERSION")
    mcp_require_auth: bool = Field(default=False, alias="MCP_REQUIRE_AUTH")

    @property
    def superuser_ids(self) -> set[int]:
        return {int(x.strip()) for x in self.superusers.split(",") if x.strip()}

    @property
    def whitelisted_groups(self) -> set[int]:
        return {int(x.strip()) for x in self.group_whitelist.split(",") if x.strip()}

    @property
    def third_party_token_map(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for item in self.third_party_tokens.split(","):
            item = item.strip()
            if not item or ":" not in item:
                continue
            name, token = item.split(":", 1)
            name = name.strip()
            token = token.strip()
            if name and token:
                result[name] = token
        return result

    @property
    def console_role_tokens(self) -> dict[str, str]:
        role_tokens = {
            "viewer": self.console_viewer_token.strip(),
            "operator": self.console_operator_token.strip(),
            "admin": self.console_admin_token.strip(),
        }
        if self.console_token.strip():
            role_tokens["admin"] = self.console_token.strip()
        return {role: token for role, token in role_tokens.items() if token}


settings = Settings()
