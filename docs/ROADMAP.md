# AnderBot 架构路线图

## 当前阶段目标

你这轮要的其实是把 AnderBot 从“能跑的机器人原型”推进到“可二开、可接入、可部署、可运营”的第一版平台骨架。

本轮落地目标：

1. **统一项目结构**：核心、适配器、集成层、控制台前后端边界清晰
2. **路线图明确**：知道先做什么、后做什么
3. **部署可启动**：Windows/Linux 一键初始化脚本
4. **控制台可见**：WebSocket 实时事件流 + 基础状态面板
5. **开放接入成型**：Webhook 与 MCP 风格调用入口先跑通
6. **NapCat 兼容增强有抓手**：先把观测和适配层位置留出来

---

## 建议目录结构

```text
anderbot/
├─ config/                    # 本地配置与运行态
├─ deploy/                    # 部署脚本（Windows / Linux）
├─ docs/                      # 设计文档、路线图、接入说明
├─ src/anderbot/
│  ├─ adapters/               # 协议适配层（NapCat / OneBot / 其他平台）
│  ├─ core/                   # 事件、模型、插件、会话、存储
│  ├─ integrations/           # Webhook / MCP / 第三方开放接入
│  ├─ plugins/                # 内置插件
│  ├─ web/                    # HTTP API + 控制台页面 + WebSocket
│  ├─ bot.py                  # 运行时装配
│  ├─ config.py               # 环境变量配置
│  └─ main.py                 # CLI 启动入口
├─ .env.example
├─ pyproject.toml
└─ README.md
```

---

## 分阶段路线图

### Phase 1：平台底座（当前）
- [x] NapCat WebSocket 接入
- [x] 插件系统
- [x] HTTP API
- [x] WebSocket 控制台基础版
- [x] Webhook 接入基础版
- [x] MCP 风格 HTTP 调用雏形
- [x] Windows/Linux 部署脚本

### Phase 2：控制台与运营能力
- [ ] 前端拆分成独立管理面板（Vue/React）
- [ ] 登录认证 / RBAC / API Token
- [ ] 事件检索、过滤、分页、归档
- [ ] 群状态开关、插件启停、配置在线编辑
- [ ] 消息发送测试台 / Webhook 调试台 / MCP 调试台

### Phase 3：开放生态
- [ ] 正式 MCP Server 协议支持（SSE / Streamable HTTP / stdio 视需求）
- [ ] Webhook 签名校验与重放保护
- [ ] 第三方应用 Token / App 管理 / 调用额度限制
- [ ] 开发者 SDK（Python / Node.js）
- [ ] 插件市场与插件签名

### Phase 4：NapCat 实战增强
- [ ] 自动重连、退避重试、心跳与连接质量监控
- [ ] API 调用结果跟踪与错误码映射
- [ ] 消息段兼容（文本、图片、at、reply、forward）
- [ ] 群权限、管理员、撤回、通知等事件兼容层
- [ ] 多协议适配抽象，为 OneBot v11/v12 预留统一接口

### Phase 5：生产化
- [ ] SQLite/PostgreSQL 持久化
- [ ] 审计日志
- [ ] 限流与风控
- [ ] 任务调度
- [ ] Docker / systemd / NSSM / PM2 等交付方式
- [ ] 监控告警（Prometheus / Grafana / Sentry）

---

## 模块职责建议

### adapters/
处理平台协议细节：NapCat 的 WebSocket 连接、事件解析、消息发送、重连策略。

### core/
平台内核，不关心 NapCat 还是别的平台。只处理统一事件、插件、会话、状态。

### integrations/
对外开放层：
- Webhook 入站
- Webhook 出站（后续）
- MCP 工具暴露
- 第三方应用接入

### web/
控制台与 HTTP API：
- `/status`
- `/console`
- `/ws/console`
- `/webhooks/*`
- `/mcp*`

---

## 你当前这一版的产出定位

这不是最终形态，而是一个**能演示、能继续扩、能开始接第三方**的第一版骨架。

适合：
- 先接 NapCat 跑起来
- 展示给别人看项目方向
- 后续继续加前端、权限、数据库、更多接入

不适合直接宣称：
- 企业级控制台
- 完整 MCP 标准实现
- 大规模生产环境高可用

---

## 接下来最值得优先做的三件事

1. **NapCat 连接增强**
   - 自动重连
   - 调用回执
   - 错误处理

2. **控制台拆前后端**
   - 前端独立项目
   - 登录鉴权
   - 事件筛选与配置编辑

3. **开放接入标准化**
   - Webhook 签名
   - MCP 正式协议化
   - 第三方应用凭证管理
