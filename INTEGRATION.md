# DeerFlow + OpenClaw 集成方案

## 目标

DeerFlow 作为大脑（任务规划 + 记忆 + IM 交互），OpenClaw 作为手（编程执行 + PTY），结合二者优点：

- ✅ DeerFlow 的沙盒稳定 + MemoryGraph 记忆 + IM 渠道
- ✅ OpenClaw 的 Codex 编程闭环 + PTY 直连

---

## 架构总览

```
用户（飞书/Telegram/浏览器）
    ↓
DeerFlow（任务规划 + 记忆 + 多Agent编排）
    ↓ 当需要编程时
invoke_acp_agent tool
    ↓ ACP协议
OpenClaw ACP Bridge（接收调用）
    ↓
OpenClaw Agent（Codex / Claude Code）
    ↓
执行结果通过 ACP 返回 DeerFlow
    ↓
DeerFlow 汇总结果 → 用户
```

---

## 方案一：DeerFlow 调用 OpenClaw（推荐）

DeerFlow 已经内置了 `invoke_acp_agent` 工具，只需要配置 OpenClaw 作为 ACP Agent 即可。

### 步骤 1：OpenClaw 启用 ACP Bridge

```bash
# 检查 OpenClaw ACP 相关配置
openclaw acp --help
```

### 步骤 2：配置 DeerFlow 的 `config.yaml`

```yaml
# config.yaml
acp_agents:
  codex:
    command: codex
    args: ["exec"]
    description: 编程Agent，负责代码编写、测试、调试
    auto_approve_permissions: true

  # 或者用 Claude Code
  claude_code:
    command: claude
    args: []
    description: 编程Agent，负责代码编写、测试、调试
    auto_approve_permissions: true
```

**但是** — OpenClaw 的 ACP 实现方式和 DeerFlow 期望的不太一样。OpenClaw ACP 是自己的协议，不是标准的 `codex exec` 接口。

### 步骤 3：需要 ACP Adapter

DeerFlow 的 `invoke_acp_agent` 期望 ACP 协议。OpenClaw 支持 ACP，但它的 command line agent 不是直接可调用的。

需要两个适配层之一：

**选项 A：用 zed-industries/codex-acp 适配器**
```bash
npx -y @zed-industries/codex-acp
```

**选项 B：用 zed-industries/claude-agent-acp 适配器**
```bash
npx -y @zed-industries/claude-agent-acp
```

### 具体配置

```yaml
# config.yaml
acp_agents:
  codex:
    command: npx
    args: ["-y", "@zed-industries/codex-acp"]
    description: Codex编程Agent（通过ACP协议调用OpenClaw Codex）
    auto_approve_permissions: true
    model: null
    env:
      CODEX_API_KEY: $OPENAI_API_KEY
```

---

## 方案二：OpenClaw Agent 作为 DeerFlow Sub-Agent

在 DeerFlow 的 Lead Agent 规划出"编程子任务"后，通过 `invoke_acp_agent` 调用 OpenClaw。

### 原理

DeerFlow 的 Agent 系统支持动态拉起 Sub-Agent：
- `subagent_enabled: true` 时，Lead Agent 可以调用 `setup_agent` 工具创建 Sub-Agent
- Sub-Agent 有独立上下文，并行执行

### 工作流

```
用户: "帮我实现一个用户登录模块"

DeerFlow Lead Agent 规划:
  ├─ 子任务1: 写代码 → invoke_acp_agent(codex, "实现用户登录...")
  ├─ 子任务2: 写测试 → invoke_acp_agent(codex, "写单元测试...")
  └─ 子任务3: 集成 → invoke_acp_agent(codex, "集成测试...")

Codex 在独立环境执行 → 结果返回 DeerFlow
DeerFlow 汇总 → 输出最终代码 + 报告
```

---

## 方案三：反向集成 — OpenClaw 调用 DeerFlow

OpenClaw 作为入口，DeerFlow 作为后端任务执行器。

### 原理

用 OpenClaw 的 `sessions_spawn` 或 DeerFlow 的 Python Client：

```python
from deerflow import DeerFlow

client = DeerFlow(base_url="http://localhost:2026")
thread = client.threads.create()
response = client.run(
    thread_id=thread.id,
    message="帮我研究一下 AI Agent 最新发展",
)
```

OpenClaw 作为大脑接收需求，调用 DeerFlow 做研究类任务。

---

## 推荐方案：方案一（DeerFlow → OpenClaw Codex）

### 完整配置步骤

#### 第一步：安装 ACP 适配器

```bash
cd ~/Desktop/poc/deer-flow

# 安装 Codex ACP 适配器
npm install -g @zed-industries/codex-acp

# 或 Claude Code ACP 适配器
npm install -g @zed-industries/claude-agent-acp
```

#### 第二步：配置 DeerFlow config.yaml

```yaml
# config.yaml
acp_agents:
  codex:
    command: npx
    args: ["-y", "@zed-industries/codex-acp", "--", "exec"]
    description: Codex编程Agent，处理复杂代码编写、测试、重构任务
    auto_approve_permissions: true
    env:
      OPENAI_API_KEY: $OPENAI_API_KEY

  claude_code:
    command: npx
    args: ["-y", "@zed-industries/claude-agent-acp"]
    description: Claude Code编程Agent，处理复杂代码编写、测试、重构任务
    auto_approve_permissions: true
    env:
      ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
```

#### 第三步：配置 OpenClaw ACP Bridge

OpenClaw 需要启用 ACP bridge 让 DeerFlow 能调用：

```bash
# 启动 OpenClaw ACP bridge
openclaw acp client --session agent:main:main
```

#### 第四步：创建编程 Skill（可选）

创建 DeerFlow Skill 专门处理编程任务：

```markdown
# skills/custom/coding/skill.md

# 编程任务处理器

当用户请求编写代码、实现功能、修复bug时使用。

## 工作流程

1. 分析需求，确定技术栈
2. 调用 `invoke_acp_agent(codex, "实现...")`
3. 收集结果
4. 如需迭代，发送修改指令

## 适用场景

- 实现新功能
- 代码重构
- 单元测试编写
- Bug修复
- 代码审查
```

---

## 关键问题与解决

### Q1: OpenClaw 的 ACP 支持是否完整？

需要验证：
- OpenClaw ACP bridge 是否支持 `invoke_acp_agent` 协议
- OpenClaw 的 `codex` agent 是否支持 ACP 协议调用

### Q2: Sandbox 内如何访问宿主机资源？

DeerFlow 的 `invoke_acp_agent` 在沙盒内执行，如果需要 OpenClaw 操作宿主机文件，需要：
- 把文件路径映射到沙盒内
- 或者让 OpenClaw Agent 在宿主机上运行（不用沙盒）

### Q3: 记忆如何共享？

两个系统的记忆是独立的：
- DeerFlow MemoryGraph → 任务规划记忆
- OpenClaw workspace → 项目文件记忆

需要在 DeerFlow 侧汇总两个系统的输出。

---

## 实施优先级

### P0（必须先验证）
1. 验证 OpenClaw ACP bridge 是否工作
2. 验证 DeerFlow 的 `invoke_acp_agent` 能否调用 OpenClaw agent
3. 测试基本的 "hello world" 调用

### P1（核心功能）
1. 配置 Codex ACP 适配器
2. 实现 DeerFlow → OpenClaw Codex 的调用链路
3. 处理返回结果

### P2（体验优化）
1. 添加编程 Skill
2. 配置记忆同步
3. 添加错误重试机制

---

## 快速验证命令

```bash
# 1. 检查 DeerFlow 是否运行
curl -s http://localhost:2026/health

# 2. 检查 OpenClaw agents
openclaw agents list

# 3. 测试 invoke_acp_agent 是否可用
curl -X POST http://localhost:2026/api/langgraph/threads \
  -H "Content-Type: application/json" \
  -d '{"assistant_id": "lead_agent"}'

# 4. 检查 codex 是否安装
which codex

# 5. 检查 npx @zed-industries/codex-acp
npm list -g @zed-industries/codex-acp
```

---

## 替代方案：直接用 DeerFlow 内置 Bash Agent

如果 ACP 集成太复杂，可以先用 DeerFlow 内置的 `bash_agent` Sub-Agent：

```yaml
# config.yaml
subagents:
  bash:
    enabled: true
```

Bash Agent 可以执行 `npx codex exec "..."`，相当于把 Codex 包装成 DeerFlow Sub-Agent。

优点：简单，DeerFlow 原生支持
缺点：没有 ACP 的结构化调用能力
