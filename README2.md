# AnderBot

AnderBot 是一个面向 **开放生态** 设计的 QQ 机器人框架：

- **NapCat WebSocket 接入**
- **插件化架构**，方便扩展指令、事件处理器、第三方服务
- **内置 Web API**，便于面板、外部系统、自动化平台联动
- **可操作 Web 控制台**，实时查看状态、事件流并直接发消息
- **Webhook / MCP 风格开放接入**
- **AI 对话插件**，兼容 OpenAI SDK 写法，可直接接 iFlow/OpenAI 兼容接口

## 这轮新增了什么

- 项目结构与路线图文档：`docs/ROADMAP.md`
- 开放接入设计文档：`docs/INTEGRATIONS.md`
- Web 控制台页面：`GET /console`
- 控制台事件流：`WS /ws/console`
- Webhook 入站：`POST /webhooks/{source}`
- MCP 风格接口：`GET /mcp`、`GET /mcp/tools`、`POST /mcp/call`
- NapCat 自动重连、发送失败统计、连接状态事件
- 控制台鉴权、Webhook 签名/Token 校验、第三方 token 映射
- NapCat 消息段 / CQ 码双向兼容
- 控制台登录页、Cookie 会话、viewer/operator/admin 分级权限
- 部署脚本：
  - Windows：`deploy/setup-windows.ps1`
  - Linux：`deploy/setup-linux.sh`
  - 启动脚本：`deploy/run-windows.bat` / `deploy/run-linux.sh`

## 快速开始

### Windows

```powershell
cd anderbot
powershell -ExecutionPolicy Bypass -File .\deploy\setup-windows.ps1
copy .env.example .env
.\.venv\Scripts\python.exe -m anderbot.main run
```

### Linux

```bash
cd /path/to/anderbot
bash ./deploy/setup-linux.sh
cp .env.example .env
source .venv/bin/activate
python -m anderbot.main run
```

## NapCat 对接

修改 `.env`：

```env
NAPCAT_WS_URL=ws://127.0.0.1:3001
NAPCAT_TOKEN=
NAPCAT_RECONNECT_BASE_SECONDS=2
NAPCAT_RECONNECT_MAX_SECONDS=30
```

确认 NapCat 已开启 WebSocket 服务，然后启动 AnderBot。连接断开后会自动指数退避重连。

### 消息段 / CQ 码兼容

- 入站消息会统一保留三种形态：
  - `raw_message`：原始文本
  - `message_segments`：标准消息段数组
  - `cq_message`：CQ 码字符串
- 出站消息支持：
  - 纯文本字符串
  - CQ 码字符串，例如：`[CQ:at,qq=123456] 你好`
  - 消息段数组，例如：

```json
[
  {"type": "reply", "data": {"id": "1001"}},
  {"type": "text", "data": {"text": "你好 "}},
  {"type": "at", "data": {"qq": "123456"}}
]
```

## Web API

默认监听：`http://0.0.0.0:8099`

### 基础接口
- `GET /status`：运行状态、插件列表、当前控制台角色信息
- `POST /send/group/{group_id}`：给群发消息，需要 `operator` 或更高权限
- `POST /send/private/{user_id}`：给私聊发消息，需要 `operator` 或更高权限

### 控制台
- `GET /console/login`：登录页
- `POST /console/login`：登录并签发 Cookie 会话
- `POST /console/logout`：退出登录
- `GET /console`：查看管理面板
- `WS /ws/console`：订阅实时事件流并执行操作
- 控制台支持：查看状态、发群消息、发私聊、广播系统消息、实时事件流

### 控制台权限模型

- `viewer`：只读看状态和事件
- `operator`：可发送群消息 / 私聊消息
- `admin`：拥有 operator 权限，并可发送控制台广播

对应环境变量：

```env
CONSOLE_VIEWER_TOKEN=viewer-secret
CONSOLE_OPERATOR_TOKEN=operator-secret
CONSOLE_ADMIN_TOKEN=admin-secret
CONSOLE_SESSION_SECRET=change-me-session-secret
```

兼容旧配置：

```env
CONSOLE_TOKEN=legacy-admin-token
```

如果设置了 `CONSOLE_TOKEN`，会自动按 `admin` 权限处理。

### 开放接入
- `POST /webhooks/{source}`：外部系统推送事件
  - 支持 `X-Webhook-Secret`
  - 支持 `X-Webhook-Signature-256: sha256=...`
  - 支持 `X-API-Token` 或 `Authorization: Bearer ...`
  - 支持按 source 映射的 `THIRD_PARTY_TOKENS`
- `GET /mcp`：查看 MCP 风格 manifest
- `GET /mcp/tools`：查看工具列表
- `POST /mcp/call`：调用工具接口

MCP 调用示例：

```json
{
  "id": "req-1",
  "tool": "send_group_message",
  "arguments": {
    "group_id": 123456,
    "message": "[CQ:at,qq=123456] hello from mcp"
  }
}
```

返回结果会尽量贴近 MCP tool result 结构。

## 推荐配置

```env
CONSOLE_VIEWER_TOKEN=replace-with-random-viewer-token
CONSOLE_OPERATOR_TOKEN=replace-with-random-operator-token
CONSOLE_ADMIN_TOKEN=replace-with-random-admin-token
CONSOLE_SESSION_SECRET=replace-with-long-random-secret
WEBHOOK_SECRET=replace-with-shared-secret
WEBHOOK_TOKEN=replace-with-global-token
THIRD_PARTY_TOKENS=github:token-1,feishu:token-2
MCP_REQUIRE_AUTH=true
```

## 当前目录结构

```text
anderbot/
├─ config/
├─ deploy/
├─ docs/
├─ src/anderbot/
│  ├─ adapters/
│  ├─ core/
│  ├─ integrations/
│  ├─ plugins/
│  ├─ web/
│  ├─ bot.py
│  ├─ config.py
│  └─ main.py
├─ .env.example
└─ pyproject.toml
```

## 下一步建议

下一轮值得继续补：

1. 控制台操作审计与命令历史
2. 真正按 MCP 规范补 `/mcp/messages`、初始化握手与 SSE/streamable transport
3. 更多 NapCat 段类型封装（forward、music、markdown、file 等）
