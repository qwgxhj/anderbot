# AnderBot Ubuntu 使用指南

## 简介

AnderBot 是一个面向开放生态设计的 QQ 机器人框架，基于 NapCat WebSocket 和 Python 插件架构。

**主要特性：**
- NapCat WebSocket 接入
- 插件化架构，方便扩展指令和事件处理器
- 内置 Web API 和控制台
- AI 对话插件（兼容 OpenAI SDK）
- Webhook / MCP 风格开放接入

---

## 系统要求

- **操作系统**: Ubuntu 20.04+ / Debian 10+
- **Python**: >= 3.11
- **NapCat**: 需要预先安装并配置 NapCat

---

## 安装步骤

### 1. 克隆或上传项目

```bash
# 如果是从 Git 克隆
git clone https://github.com/qwgxhj/anderbot.git
cd anderbot

# 或者直接将项目上传到服务器，然后进入目录
cd /path/to/anderbot
```

### 2. 运行安装脚本

```bash
bash ./deploy/setup-linux.sh
```

这个脚本会自动完成：
- 创建 Python 虚拟环境 (`.venv`)
- 安装依赖包
- 复制 `.env.example` 到 `.env`（如果不存在）

### 3. 配置环境变量

编辑 `.env` 文件：

```bash
nano .env
```

**关键配置项：**

```env
# NapCat WebSocket 配置（必需）
NAPCAT_WS_URL=ws://127.0.0.1:1145
NAPCAT_TOKEN=your_napcat_token

# AnderBot 服务配置
ANDERBOT_HOST=0.0.0.0
ANDERBOT_PORT=8099

# 超级用户 QQ 号（逗号分隔）
SUPERUSERS=123456789,987654321

# AI 对话配置（可选）
OPENAI_BASE_URL=https://apis.iflow.cn/v1
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=TBStars2-200B-A13B

# 控制台权限配置（建议设置）
CONSOLE_VIEWER_TOKEN=your-viewer-token
CONSOLE_OPERATOR_TOKEN=your-operator-token
CONSOLE_ADMIN_TOKEN=your-admin-token
CONSOLE_SESSION_SECRET=your-session-secret

# Webhook 安全配置
WEBHOOK_SECRET=your-webhook-secret
WEBHOOK_TOKEN=your-webhook-token
```

### 4. 启动服务

**方式一：使用启动脚本**

```bash
bash ./deploy/run-linux.sh
```

**方式二：手动启动**

```bash
source .venv/bin/activate
python -m anderbot.main run
```

---

## NapCat 配置

在使用 AnderBot 之前，需要先配置并启动 NapCat：

### 1. 安装 NapCat

参考 NapCat 官方文档进行安装。

### 2. 配置 NapCat WebSocket

在 NapCat 配置中启用 WebSocket 服务：

```json
{
  "ws": {
    "enable": true,
    "host": "127.0.0.1",
    "port": 1145
  }
}
```

### 3. 启动 NapCat

确保 NapCat 正常运行并监听 WebSocket 端口。

---

## 常用命令

### 启动机器人

```bash
cd /path/to/anderbot
bash ./deploy/run-linux.sh
```

### 更新依赖

```bash
cd /path/to/anderbot
source .venv/bin/activate
pip install -e .
```

### 查看日志

如果需要在后台运行并查看日志：

```bash
# 使用 nohup
nohup bash ./deploy/run-linux.sh > anderbot.log 2>&1 &

# 查看日志
tail -f anderbot.log
```

### 使用 systemd 服务（推荐用于生产环境）

创建服务文件：

```bash
sudo nano /etc/systemd/system/anderbot.service
```

内容：

```ini
[Unit]
Description=AnderBot QQ Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/anderbot
Environment=PATH=/path/to/anderbot/.venv/bin
ExecStart=/path/to/anderbot/.venv/bin/python -m anderbot.main run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable anderbot
sudo systemctl start anderbot

# 查看状态
sudo systemctl status anderbot

# 查看日志
sudo journalctl -u anderbot -f
```

---

## Web API 接口

默认监听地址：`http://0.0.0.0:8099`

### 基础接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/status` | GET | 运行状态、插件列表 |
| `/send/group/{group_id}` | POST | 发送群消息 |
| `/send/private/{user_id}` | POST | 发送私聊消息 |

### 控制台

| 接口 | 方法 | 说明 |
|------|------|------|
| `/console` | GET | Web 控制台页面 |
| `/ws/console` | WS | 实时事件流 |
| `/console/login` | POST | 登录 |

### 开放接入

| 接口 | 方法 | 说明 |
|------|------|------|
| `/webhooks/{source}` | POST | 外部系统推送事件 |
| `/mcp` | GET | MCP manifest |
| `/mcp/tools` | GET | 工具列表 |
| `/mcp/call` | POST | 调用工具 |

---

## 插件开发

插件位于 `src/anderbot/plugins/` 目录。

**示例插件结构：**

```python
# src/anderbot/plugins/my_plugin.py
from anderbot.core.plugin_base import Plugin

class MyPlugin(Plugin):
    name = "my_plugin"
    
    async def on_message(self, message):
        if message.content == "/hello":
            await message.reply("Hello!")
```

---

## 故障排查

### 1. 无法连接 NapCat

- 检查 NapCat 是否已启动
- 检查 `NAPCAT_WS_URL` 配置是否正确
- 检查防火墙设置

```bash
# 测试 NapCat WebSocket 连接
curl http://127.0.0.1:3001
```

### 2. 端口被占用

```bash
# 查看端口占用
sudo lsof -i :8099

# 或更换端口（修改 .env 中的 ANDERBOT_PORT）
```

### 3. 权限问题

```bash
# 确保脚本有执行权限
chmod +x ./deploy/setup-linux.sh
chmod +x ./deploy/run-linux.sh
```

### 4. Python 版本问题

```bash
# 检查 Python 版本
python3 --version

# 如果版本过低，安装 Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
```

---

## 目录结构

```
anderbot/
├── config/           # 配置文件
├── deploy/           # 部署脚本
│   ├── setup-linux.sh
│   └── run-linux.sh
├── docs/             # 文档
├── src/anderbot/     # 源代码
│   ├── adapters/     # 适配器（NapCat）
│   ├── core/         # 核心模块
│   ├── integrations/ # 集成服务
│   ├── plugins/      # 插件
│   ├── web/          # Web API
│   ├── bot.py        # 机器人主类
│   ├── config.py     # 配置类
│   └── main.py       # 入口文件
├── .env              # 环境变量（需创建）
├── .env.example      # 环境变量示例
└── pyproject.toml    # 项目配置
```

---

## 安全建议

1. **修改默认 Token**：生产环境务必修改所有 `CONSOLE_*_TOKEN`
2. **设置防火墙**：限制 Web API 端口的访问
3. **使用 HTTPS**：生产环境建议配合 Nginx 反向代理使用 HTTPS
4. **定期更新**：保持 NapCat 和 AnderBot 更新到最新版本

---

## 参考链接

- [NapCat 文档](https://napneko.github.io/)
- [项目文档](./docs/)
