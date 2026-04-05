---
artifact: execute-log
task: research-team-collaboration
date: 2026-04-05
role: backend-engineer
status: draft
---

# 研究团队协作系统 - 实施日志

## 计划 vs 实际

### 计划工作项（Day 1-2 后端基础设施）

| 工作项 | 计划 | 实际 | 偏差 |
|--------|------|------|------|
| SQLite ORM 层 (`database.py`) | Day 1 | Day 1 | ✅ 完成 |
| Pydantic 模型 (`models.py`) | Day 1 | Day 1 | ✅ 完成 |
| 线程安全 Client (`client_safe.py`) | Day 1 | Day 1 | ✅ 完成 |
| API 路由骨架 (`routers/research.py`) | Day 1-2 | Day 2 | ✅ 完成 |
| 研究团队改造（异步化） | Day 2 | Day 2 | ✅ 完成 |

### 实际产出

1. **新增文件**：
   - `backend/research_team/models.py` - Pydantic 模型和 dataclass 实体
   - `backend/research_team/database.py` - SQLite ORM 层
   - `backend/research_team/client_safe.py` - 线程安全 DeerFlowClient 包装
   - `backend/research_team/project_manager.py` - 异步任务管理器
   - `backend/app/gateway/routers/research.py` - FastAPI 路由

2. **修改文件**：
   - `backend/research_team/__init__.py` - 新增导出
   - `backend/app/gateway/app.py` - 注册 research 路由

---

## 关键决定

### 决定 1: 线程安全方案

**问题**：DeerFlowClient 非线程安全

**决策**：使用 `threading.local()` 为每个线程创建独立实例

**实现**：
```python
# client_safe.py
_thread_local = threading.local()

def get_client() -> DeerFlowClient:
    if not hasattr(_thread_local, "client"):
        _thread_local.client = DeerFlowClient(...)
    return _thread_local.client
```

**为什么**：简单有效，避免全局锁的性能损失

### 决定 2: 异步任务执行

**问题**：原有 `team.run()` 是同步阻塞，不支持进度追踪

**决策**：使用 FastAPI `BackgroundTasks` + 自定义 `AsyncResearchTeam`

**为什么**：`BackgroundTasks` 是 FastAPI 原生支持，与现有架构一致

### 决定 3: 进度更新机制

**问题**：如何让前端知道研究进度

**决策**：数据库持久化 + 轮询 API

**实现**：
- 每个阶段更新 `progress` 和 `current_phase`
- 前端每分钟轮询 `GET /api/research/projects/{id}`

---

## 阻塞与解决

### 阻塞 1: 异步改造复杂度

**问题**：将同步的 `ResearchTeam.run()` 改造为异步

**解决**：
- 新增 `AsyncResearchTeam` 类，不破坏原有 `ResearchTeam`
- 保持原有同步接口兼容
- 新增 `ProjectManager` 管理异步任务

**状态**：✅ 已解决

### 阻塞 2: DeerFlowClient 线程安全

**问题**：多线程并发调用同一 DeerFlowClient 实例会导致竞态

**解决**：
- 使用线程本地存储（`threading.local()`）
- 每个线程第一次调用时创建独立实例
- 后续调用复用同一实例

**状态**：✅ 已解决

### 阻塞 3: user_id 获取方式（用户确认后）

**问题**：API 需要前端传入 user_id，但应该从鉴权层获取

**解决**：
- 从请求头 `X-User-ID` 获取用户身份
- 前端从会话获取并传递该请求头
- 后端不依赖前端传入 user_id

**状态**：✅ 已解决（用户确认：鉴权方式）

---

## 影响面

### 后端

| 模块 | 影响 | 说明 |
|------|------|------|
| `research_team/` | 扩展 | 新增 4 个模块 |
| `app/gateway/` | 扩展 | 新增 research 路由 |
| `deerflow` | 无 | 无依赖变更 |

### 前端

| 影响 | 说明 |
|------|------|
| API 契约 | 6 个新端点（见 arch-design.md） |
| 路由 | `/api/research/*` |

### 数据库

| 影响 | 说明 |
|------|------|
| 新建表 | `research_projects` |
| 迁移 | 自动创建（无破坏性变更） |

---

## 未完成项

| 项 | 原因 | 计划 |
|----|------|------|
| 中间产出 API (`/outputs`) | 需要新增 `research_outputs` 表存储中间产出（已确认方案：DB 存储） | Day 5 |
| 任务取消功能 | 需要任务中断机制，稍后实现 | Day 5 |
| 前端 UI | 属于前端阶段 | Day 4-6 |
| X-User-ID 鉴权中间件 | 当前仅做了 header 接收，需要实际的鉴权中间件设置该头 | 待实现 |

---

## 自测结果

### 导入测试 ✅

```bash
$ source .venv/bin/activate
$ python -c "from research_team.models import ResearchPhase; print('OK')"
OK
```

### 应用创建测试 ✅

```bash
$ python -c "from app.gateway.app import create_app; app = create_app(); print('OK')"
OK
```

### 路由注册测试 ✅

```bash
$ python -c "
from app.gateway.app import create_app
app = create_app()
routes = [r.path for r in app.routes if hasattr(r, 'path')]
print([r for r in routes if 'research' in r])
"
['/api/research/projects', '/api/research/projects', '/api/research/projects/{project_id}', '/api/research/projects/{project_id}/outputs', '/api/research/projects/{project_id}/report']
```

---

## 下游交接

### 交接给 QA

**待测内容**：
1. API 端点功能（使用 curl 或 Postman）
2. 数据库持久化
3. 多用户数据隔离

**测试用例**：
- `POST /api/research/projects` - 创建项目
- `GET /api/research/projects?user_id=xxx` - 列表
- `GET /api/research/projects/{id}` - 详情
- `GET /api/research/projects/{id}/report` - 报告

### 交接给前端

**API 契约**：见 `arch-design.md` 第 4 节

**待对接端点**：
- `POST /api/research/projects` - 创建项目
- `GET /api/research/projects` - 列表
- `GET /api/research/projects/{id}` - 详情
- `GET /api/research/projects/{id}/report` - 报告

---

## 风险记录

| 风险 | 等级 | 状态 | 说明 |
|------|------|------|------|
| DeerFlowClient 线程安全 | 高 | ✅ 已缓解 | 使用线程本地存储 |
| SQLite 并发写入 | 中 | ✅ 已缓解 | WAL 模式 + busy_timeout |
| 长任务超时 | 中 | ⚠️ 待验证 | 尚未实际运行长时间任务 |
