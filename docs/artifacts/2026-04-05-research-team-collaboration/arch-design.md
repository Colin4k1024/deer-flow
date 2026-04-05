---
artifact: arch-design
task: research-team-collaboration
date: 2026-04-05
role: architect
status: draft
---

# 研究团队协作系统 - 架构设计

## 1. 系统边界

### 与 DeerFlow 主系统的边界

```
┌─────────────────────────────────────────────────────────────┐
│                    DeerFlow 主系统                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ LangGraph   │  │ Gateway API │  │ Frontend        │   │
│  │ Server      │  │ (FastAPI)   │  │ (Next.js)       │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 扩展点：新增 research router
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               研究团队协作系统（新增长）                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Gateway API (FastAPI)                   │   │
│  │   └── routers/research.py (新增)                    │   │
│  │       - POST /api/research/projects                  │   │
│  │       - GET  /api/research/projects                 │   │
│  │       - GET  /api/research/projects/{id}            │   │
│  │       - DELETE /api/research/projects/{id}         │   │
│  │       - GET  /api/research/projects/{id}/outputs   │   │
│  │       - GET  /api/research/projects/{id}/report    │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           backend/research_team/ (扩展)               │   │
│  │   ├── research_team.py    - ResearchTeam (改造)     │   │
│  │   ├── project_manager.py  - 项目管理器 (新增)         │   │
│  │   ├── database.py         - SQLite ORM层 (新增)      │   │
│  │   └── models.py           - Pydantic模型 (新增)      │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           backend/research_outputs/ (存储)           │   │
│  │   └── {project_id}_final.md                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**边界原则**：
- 研究团队模块 (`research_team/`) 保持独立，不直接依赖 Gateway API
- 通过 `DeerFlowClient` 与 DeerFlow 核心交互
- 数据持久化独立于 DeerFlow 现有 thread storage

---

## 2. 组件拆分

### 目录结构

```
backend/
├── research_team/
│   ├── __init__.py                    # 导出 ResearchTeam, ProjectManager
│   ├── research_team.py               # ResearchTeam (改造：支持异步)
│   ├── project_manager.py             # 项目管理器 (新增)
│   ├── database.py                    # SQLite ORM层 (新增)
│   ├── models.py                     # Pydantic + dataclass 模型 (新增)
│   ├── client_safe.py                # 线程安全 Client 包装 (新增)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── lead_researcher.py
│   │   ├── information_collector.py
│   │   ├── analyst.py
│   │   ├── report_writer.py
│   │   └── reviewer.py
│   └── run_research.py               # CLI (保持不变)
│
├── research_outputs/                  # 报告存储目录
│   └── {project_id}_final.md
│
└── app/gateway/
    └── routers/
        └── research.py               # FastAPI 路由 (新增)
```

### 组件职责

| 组件 | 职责 | 边界 |
|------|------|------|
| `database.py` | SQLite CRUD，WAL模式，连接池 | 只被 `project_manager.py` 调用 |
| `models.py` | Pydantic 请求/响应模型，dataclass 实体 | 被所有层使用 |
| `client_safe.py` | DeerFlowClient 线程安全包装 | 每个任务独立实例 |
| `project_manager.py` | 任务调度，状态持久化，进度更新 | 核心编排层 |
| `research.py` (router) | HTTP API，参数校验，BackgroundTasks | 只调用 `project_manager` |
| `research_team.py` | Agent 协作流程 (改造：异步化) | 被 `project_manager` 调用 |

---

## 3. 关键数据流

### 研究任务完整生命周期

```
用户提交请求
    │
    ▼
POST /api/research/projects
    │
    ▼
┌─────────────────────────────────────────┐
│ 1. 创建项目记录 (SQLite)                 │
│    status = PENDING                      │
│    user_id = 当前用户                    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 2. BackgroundTasks 调度后台任务          │
│    task = project_manager.run_async()    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 3. 项目状态更新                          │
│    status = IN_PROGRESS (10%)           │
│    progress 更新每阶段                    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 4. 研究流程 (异步)                       │
│    ├─ 阶段1: 制定计划 (20%)             │
│    ├─ 阶段2: 并行搜集 (40%)             │
│    ├─ 阶段3: 并行分析 (60%)             │
│    ├─ 阶段4: 报告撰写 (80%)             │
│    └─ 阶段5: 审核 (90%)                 │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 5. 最终报告写入                          │
│    path = research_outputs/{id}_final.md │
│    status = COMPLETED (100%)            │
└─────────────────────────────────────────┘
    │
    ▼
用户轮询获取结果
    │
    ▼
GET /api/research/projects/{id}/report
```

### 项目状态机

```
PENDING → IN_PROGRESS → COMPLETED
    │           │
    │           ├→ FAILED (出错)
    │           └→ CANCELLED (用户取消)
    │
    └──────────→ CANCELLED (取消)
```

---

## 4. 接口约定

### REST API 契约

#### 4.1 创建研究项目
```
POST /api/research/projects
Content-Type: application/json

Request:
{
  "topic": "2026年协作机器人发展趋势",
  "directions": ["技术趋势", "市场分析", "应用案例"],
  "user_id": "user_123"
}

Response 201:
{
  "project_id": "proj_abc123",
  "status": "PENDING",
  "created_at": "2026-04-05T10:00:00Z",
  "message": "项目已创建，研究团队正在启动"
}
```

#### 4.2 列出用户项目
```
GET /api/research/projects?user_id=user_123

Response 200:
{
  "projects": [
    {
      "project_id": "proj_abc123",
      "topic": "2026年协作机器人发展趋势",
      "status": "IN_PROGRESS",
      "progress": 40,
      "created_at": "2026-04-05T10:00:00Z",
      "updated_at": "2026-04-05T10:15:00Z"
    }
  ],
  "total": 1
}
```

#### 4.3 获取项目详情
```
GET /api/research/projects/{project_id}

Response 200:
{
  "project_id": "proj_abc123",
  "topic": "2026年协作机器人发展趋势",
  "directions": ["技术趋势", "市场分析", "应用案例"],
  "status": "IN_PROGRESS",
  "progress": 40,
  "current_phase": "信息搜集",
  "created_at": "2026-04-05T10:00:00Z",
  "updated_at": "2026-04-05T10:15:00Z"
}
```

#### 4.4 取消项目
```
DELETE /api/research/projects/{project_id}

Response 200:
{
  "project_id": "proj_abc123",
  "status": "CANCELLED",
  "message": "项目已取消"
}
```

#### 4.5 获取中间产出
```
GET /api/research/projects/{project_id}/outputs

Response 200:
{
  "project_id": "proj_abc123",
  "outputs": [
    {
      "phase": "信息搜集",
      "direction": "技术趋势",
      "content": "...",
      "created_at": "2026-04-05T10:10:00Z"
    }
  ]
}
```

#### 4.6 获取最终报告
```
GET /api/research/projects/{project_id}/report

Response 200:
{
  "project_id": "proj_abc123",
  "report": "# 2026年协作机器人发展趋势\n\n## 执行摘要\n...",
  "format": "markdown",
  "word_count": 12500
}
```

### 错误码约定

| HTTP Status | Error Code | 说明 |
|-------------|------------|------|
| 400 | INVALID_REQUEST | 参数错误 |
| 401 | UNAUTHORIZED | 未认证 |
| 403 | FORBIDDEN | 无权限访问该项目 |
| 404 | NOT_FOUND | 项目不存在 |
| 409 | CONFLICT | 状态冲突（如重复创建） |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 5. 技术选型

### SQLite 方案

**选型理由**：
- 轻量无需额外部署
- 写入并发需求不高（研究任务相对低频）
- 支持 WAL 模式提升并发读性能

**配置**：
```python
# database.py
import aiosqlite

DB_PATH = "research_team.db"
CONNECTION_pool_SIZE = 5
BUSY_TIMEOUT = 30000  # 30秒

# 初始化
await aiosqlite.connect(DB_PATH, isolation_level=None)
# PRAGMA journal_mode=WAL
# PRAGMA busy_timeout=30000
```

**表结构**：
```sql
CREATE TABLE research_projects (
    project_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    directions TEXT NOT NULL,  -- JSON 数组
    status TEXT NOT NULL DEFAULT 'PENDING',
    progress INTEGER NOT NULL DEFAULT 0,
    current_phase TEXT,
    final_report_path TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_projects_user_id ON research_projects(user_id);
CREATE INDEX idx_projects_status ON research_projects(status);
```

### 线程安全方案

**问题**：`DeerFlowClient` 非线程安全，同一实例被多线程并发访问会出问题。

**方案**：为每个并发任务创建独立 `DeerFlowClient` 实例。

```python
# client_safe.py
from packages.harness.deerflow.client import DeerFlowClient
import threading

_thread_local = threading.local()

def get_client() -> DeerFlowClient:
    """获取当前线程独立的 DeerFlowClient 实例"""
    if not hasattr(_thread_local, 'client'):
        _thread_local.client = DeerFlowClient(
            model_name="minimax-m2.7-highspeed",
            thinking_enabled=True,
            subagent_enabled=True,
        )
    return _thread_local.client
```

### 异步任务方案

**选型**：FastAPI `BackgroundTasks`

**理由**：
- 轻量无需额外消息队列
- 与 FastAPI 原生集成
- 支持任务取消

```python
# project_manager.py
from fastapi import BackgroundTasks

async def run_async(project_id: str):
    """异步执行研究任务"""
    project = await db.get_project(project_id)
    await db.update_status(project_id, "IN_PROGRESS", progress=10)

    try:
        # 调用研究团队（需改造为 async）
        team = AsyncResearchTeam(project)
        await team.run()
    except Exception as e:
        await db.update_status(project_id, "FAILED", error=str(e))
```

---

## 6. 风险与约束

### 高风险（Critical）

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| **DeerFlowClient 线程安全** | 多线程并发调用同一实例会导致竞态条件 | 每个线程独立实例（见 5.3 方案） |
| **长任务超时** | 研究任务可能需要数分钟到数小时 | 心跳机制（每分钟更新 progress）+ 前端超时提示 |
| **SQLite 并发写入** | 多用户同时创建项目可能冲突 | WAL 模式 + busy_timeout |

### 中风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| **研究报告存储** | 多实例部署时无法共享 | 本地存储仅适合单机部署；多实例需 NFS 或对象存储 |
| **用户鉴权** | 当前无用户概念 | user_id 从请求头/上下文获取，暂时用 mock |

### 约束

1. **单实例部署**：当前设计仅支持单机部署（报告存储在本地文件系统）
2. **任务不可迁移**：后台任务一旦开始不能在实例间迁移
3. **无任务重试**：失败后需用户手动重新创建

---

## 7. 实施路线图

### 阶段 1：后端基础设施（Day 1-2）

**目标**：完成数据库层 + API 路由

**任务**：
- [ ] 新增 `database.py`：SQLite ORM 层
- [ ] 新增 `models.py`：Pydantic 模型
- [ ] 新增 `client_safe.py`：线程安全 Client
- [ ] 新增 `routers/research.py`：FastAPI 路由
- [ ] 改造 `research_team.py`：支持异步 + 进度回调

**验收标准**：
- API 端点可调用
- 项目可创建和查询
- 状态持久化到 SQLite

### 阶段 2：研究编排器改造（Day 3-5）

**目标**：将 ResearchTeam 改造为异步 + 可中断

**任务**：
- [ ] 改造 `project_manager.py`：异步任务管理器
- [ ] 改造 `research_team.py`：异步执行流程
- [ ] 实现进度更新机制（每阶段回调）
- [ ] 实现任务取消机制
- [ ] 实现心跳机制（防止任务"假死"）

**验收标准**：
- 后台任务可正常执行
- 进度可实时查询
- 任务可取消

### 阶段 3：前端 + 集成（Day 6-7）

**目标**：完成前端 UI + 端到端测试

**任务**：
- [ ] 研究任务创建页
- [ ] 研究列表页
- [ ] 研究详情页
- [ ] 报告查看器
- [ ] 端到端测试

**验收标准**：
- 用户可完整走完研究任务流程
- 报告可正常生成和下载

---

## 8. 未决项

| 项 | 状态 | 负责人 |
|----|------|--------|
| 多实例部署时报告共享方案 | 待定 | architect |
| 用户鉴权的具体实现方式 | 待定 | backend-engineer |
| 任务超时阈值设定 | 待定 | product-manager |
