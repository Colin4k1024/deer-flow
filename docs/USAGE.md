# DeerFlow 2.0 使用文档

> 项目路径：`/Users/jiafan/Desktop/poc/deer-flow`
> 官网：https://deerflow.tech
> GitHub：https://github.com/bytedance/deer-flow

---

## 什么是 DeerFlow？

DeerFlow（Deep Exploration and Efficient Research Flow）是一个开源的 **Super Agent Harness**。

它把 **Sub-Agents**、**Memory** 和 **Sandbox** 组织在一起，再配合可扩展的 **Skills**，让 AI Agent 可以完成复杂的多步骤任务——不只是聊天，而是真正"有一台自己的电脑"。

核心能力：
- **多模型支持**：支持 OpenAI、Claude、Doubao-Seed、DeepSeek、Kimi 等
- **Sub-Agents 并行**：复杂任务自动拆解，多路并行执行
- **沙盒执行**：任务运行在隔离的 Docker 容器里，可审计、不互相污染
- **Skills 扩展**：内置多种 Skills（研究、报告生成、PPT、网页、图片视频生成），支持自定义
- **IM 渠道接入**：支持 Telegram、Slack、飞书，直接在聊天窗口和 DeerFlow 交互
- **长期记忆**：基于 MemoryGraph 的因果记忆系统

---

## 快速安装

### 前提条件

| 工具 | 版本要求 |
|------|----------|
| Python | 3.12+ |
| Node.js | 22+ |
| pnpm | 最新版 |
| uv | 最新版 |
| nginx | 最新版 |
| Docker | 可选（推荐） |

检查环境：
```bash
cd /Users/jiafan/Desktop/poc/deer-flow
make check
```

### 配置

```bash
# 1. 生成本地配置文件
make config

# 2. 编辑 config.yaml，添加模型配置
#    推荐模型：Doubao-Seed-2.0-Code、DeepSeek v3.2、Kimi 2.5
```

配置示例（`config.yaml`）：
```yaml
models:
  - name: gpt-4
    display_name: GPT-4
    use: langchain_openai:ChatOpenAI
    model: gpt-4
    api_key: $OPENAI_API_KEY
    max_tokens: 4096
    temperature: 0.7
```

### 安装依赖

```bash
make install
```

### 运行

**方式一：Docker（推荐）**
```bash
make docker-init   # 拉取沙盒镜像（首次）
make docker-start  # 启动服务
```

**方式二：本地开发**
```bash
make dev
```

访问地址：**http://localhost:2026**

---

## 项目结构

```
deer-flow/
├── backend/                      # Python 后端（LangGraph + FastAPI）
│   ├── app/
│   │   ├── channels/             # IM 渠道（Telegram、Slack、飞书）
│   │   └── gateway/              # Gateway API 路由
│   ├── packages/harness/deerflow/  # 核心 harness 包
│   │   ├── agents/              # Agent 定义（lead agent、sub-agents）
│   │   ├── client.py             # Python Client
│   │   ├── community/            # 社区扩展（sandbox providers）
│   │   ├── config/               # 配置加载
│   │   ├── mcp/                  # MCP Server 集成
│   │   ├── models/              # 模型封装
│   │   ├── sandbox/              # 沙盒执行
│   │   ├── skills/              # Skills 加载
│   │   ├── subagents/           # Sub-Agent 管理
│   │   ├── tools/               # 核心工具（搜索、爬虫、bash、文件）
│   │   └── uploads/             # 文件上传
│   ├── docs/                    # 详细设计文档
│   └── tests/                   # 测试用例
│
├── frontend/                     # Next.js 前端
│   ├── src/
│   │   ├── app/                 # 页面（/workspace、/api）
│   │   ├── components/          # React 组件
│   │   ├── core/                # 核心逻辑
│   │   │   ├── agents/          # Agent 配置
│   │   │   ├── api/             # API 封装
│   │   │   ├── artifacts/       # 内容渲染（Markdown、代码块）
│   │   │   ├── config/          # 前端配置
│   │   │   ├── i18n/            # 国际化
│   │   │   ├── memory/          # 记忆管理
│   │   │   ├── models/          # 模型配置
│   │   │   ├── mcp/             # MCP 集成
│   │   │   ├── settings/        # 设置页面
│   │   │   ├── skills/          # Skills 管理
│   │   │   ├── threads/         # 线程管理
│   │   │   └── uploads/         # 文件上传
│   │   └── hooks/               # React Hooks
│   └── public/                  # 静态资源
│
├── skills/                       # Skills 文件
│   └── public/                  # 内置 Skills
│       ├── research/
│       ├── report-generation/
│       ├── slide-creation/
│       ├── web-page/
│       ├── image-generation/
│       └── claude-to-deerflow/  # Claude Code 集成
│
├── scripts/                      # 构建和部署脚本
├── docs/                         # 项目文档
├── config.example.yaml           # 配置模板
├── config.yaml                   # 本地配置（生成）
├── docker/                       # Docker 相关文件
└── Makefile                      # 常用命令
```

---

## 核心模块说明

### 1. Agent 系统

```
Lead Agent（主控 Agent）
  └─ 按需拉起 Sub-Agents
       ├─ Sub-Agent A（独立上下文）
       ├─ Sub-Agent B（独立上下文）
       └─ Sub-Agent C（独立上下文）
```

- **Lead Agent**：负责任务规划、分拆、汇总结果
- **Sub-Agents**：各自独立上下文，并行执行子任务
- 支持动态扩缩，根据任务复杂度自动调整

### 2. Sandbox 执行

每个任务运行在隔离的 Docker 容器里：

```
容器内路径：
/mnt/
├── skills/           # Skills 文件
│   ├── public/       # 内置 Skills
│   └── custom/       # 自定义 Skills
├── user-data/
│   ├── uploads/      # 上传文件
│   ├── workspace/    # 工作目录
│   └── outputs/      # 输出结果
```

### 3. Skills 系统

Skills 是 DeerFlow 扩展能力的关键。每个 Skill 是一个结构化的 Markdown 文件，定义了工作流、最佳实践和参考资源。

内置 Skills：
| Skill | 用途 |
|-------|------|
| `research` | 深度研究 |
| `report-generation` | 报告生成 |
| `slide-creation` | PPT 制作 |
| `web-page` | 网页生成 |
| `image-generation` | 图片生成 |

### 4. IM 渠道

配置完成后，可以直接在聊天软件里和 DeerFlow 交互：

| 渠道 | 配置难度 |
|------|----------|
| Telegram | 简单 |
| Slack | 中等 |
| 飞书 | 中等 |

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `make config` | 生成本地配置 |
| `make check` | 检查环境依赖 |
| `make install` | 安装所有依赖 |
| `make dev` | 本地开发模式启动 |
| `make docker-init` | 拉取沙盒镜像 |
| `make docker-start` | Docker 开发模式启动 |
| `make docker-stop` | 停止 Docker 服务 |
| `make up` | 生产环境启动 |
| `make down` | 停止生产环境 |
| `make stop` | 停止本地服务 |
| `make clean` | 清理临时文件 |

---

## 环境变量

在 `.env` 文件中配置：

```bash
# 必需
OPENAI_API_KEY=your-openai-api-key

# 可选：Tavily 搜索
TAVILY_API_KEY=your-tavily-api-key

# 可选：LangSmith 链路追踪
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key

# IM 渠道（按需配置）
TELEGRAM_BOT_TOKEN=your-telegram-token
SLACK_BOT_TOKEN=your-slack-bot-token
SLACK_APP_TOKEN=your-slack-app-token
FEISHU_APP_ID=your-feishu-app-id
FEISHU_APP_SECRET=your-feishu-app-secret
```

---

## Python Client

DeerFlow 提供了 Python Client，可以编程调用：

```python
from deerflow import DeerFlow

client = DeerFlow(base_url="http://localhost:2026")

# 创建线程
thread = client.threads.create()
print(f"Thread ID: {thread.id}")

# 发送消息
response = client.run(
    thread_id=thread.id,
    message="帮我研究一下 AI Agent 的最新发展",
    assistant_id="lead_agent",
)
print(response)
```

---

## 开发相关

### 路由结构

```
http://localhost:2026
├── /                    # 首页
├── /workspace           # 工作区
├── /api/               # API 代理
│   ├── /chat            # 对话
│   ├── /threads         # 线程管理
│   ├── /memory          # 记忆管理
│   └── /config          # 配置
└── /api/langgraph      # LangGraph API
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 15, React 19, TailwindCSS, shadcn/ui |
| 后端 | Python 3.12+, LangGraph, LangChain, FastAPI |
| Agent | LangGraph (StateGraph)、Sub-Agents |
| 沙盒 | Docker, Kubernetes (可选) |
| 部署 | Docker Compose, Nginx |

---

## FAQ

**Q: Docker 模式下服务起不来？**
A: 先执行 `make docker-init` 拉取沙盒镜像，然后再 `make docker-start`。

**Q: 如何切换模型？**
A: 编辑 `config.yaml` 中的 `models` 配置项，支持多模型切换。

**Q: 如何添加自定义 Skill？**
A: 在 `/mnt/skills/custom/` 目录下添加 Skill 文件（Markdown 格式）。

**Q: 支持哪些模型？**
A: 支持所有 LangChain 兼容模型，包括 OpenAI、Claude、Doubao-Seed、DeepSeek、Kimi 等。

**Q: IM 渠道需要公网 IP 吗？**
A: 不需要。Telegram 使用 Long Polling，Slack 使用 Socket Mode，飞书使用 WebSocket，都不需要公网 IP。
