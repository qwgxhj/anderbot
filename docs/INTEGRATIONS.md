# AnderBot 开放接入设计

## 1. Webhook

### 入站接口

- `POST /webhooks/{source}`

用途：
- 外部平台把事件推给 AnderBot
- 管理后台、自动化平台、第三方系统触发机器人动作

建议请求头：
- `Content-Type: application/json`
- `X-Webhook-Secret: <secret>`

当前实现：
- 支持基础密钥校验
- 接收到的 payload 会进入控制台事件流

后续增强：
- HMAC 签名
- 时间戳防重放
- source 级别权限
- source 级别路由

---

## 2. MCP 风格接口

### Manifest
- `GET /mcp`

### 调用
- `POST /mcp/call`

请求示例：

```json
{
  "tool": "send_group_message",
  "arguments": {
    "group_id": 123456,
    "message": "hello from mcp"
  }
}
```

当前内置工具：
- `status`
- `plugins`
- `send_group_message`
- `send_private_message`

后续增强：
- 正式 MCP 协议对象
- SSE / Streamable HTTP
- Tool schema 自动生成
- 插件自动暴露 MCP tools
- 权限与额度控制

---

## 3. 第三方开放接入

建议后续补这些对象：

### app registration
- app_id
- app_secret
- app_name
- scopes
- rate_limit
- callback_urls

### scopes 示例
- `bot:status:read`
- `bot:plugins:read`
- `bot:message:send`
- `bot:webhook:write`
- `bot:console:read`

### 典型开放能力
- 机器人状态查询
- 发送群消息 / 私聊消息
- 读取插件清单
- 触发指定插件动作
- 订阅事件推送

---

## 4. 推荐演进路径

第一步：先把 HTTP API / Webhook / MCP 雏形跑通
第二步：增加 auth/token/app registry
第三步：把插件能力标准化为 tool / action / event
第四步：做开发者文档与 SDK
