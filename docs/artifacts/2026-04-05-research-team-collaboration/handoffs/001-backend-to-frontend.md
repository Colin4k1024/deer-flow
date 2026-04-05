---
artifact: handoff
task: research-team-collaboration
date: 2026-04-05
role: backend-engineer
status: draft
---

# Handoff: Backend → Frontend

## 交接信息

| 字段 | 值 |
|------|-----|
| 来自角色 | backend-engineer |
| 目标角色 | frontend-engineer |
| 交接时间 | 2026-04-05 |
| 当前阶段 | execute |
| 目标阶段 | review |
| 就绪状态 | ready-for-review |
| 阻塞项 | 无 |

---

## 背景

研究团队协作系统后端基础设施已完成，需要交接给前端工程师进行 UI 开发。

**项目目标**：用户通过 Web UI 发布研究任务 → 系统自动组建研究团队 → 多 Agent 协作完成 → 用户获取研究报告

---

## 输入依据

### 已完成的后端产出

1. **API 端点**（6 个，已注册到 FastAPI）：
   ```
   POST   /api/research/projects              # 创建项目
   GET    /api/research/projects              # 列表
   GET    /api/research/projects/{project_id} # 详情
   DELETE /api/research/projects/{project_id} # 取消
   GET    /api/research/projects/{project_id}/outputs  # 中间产出
   GET    /api/research/projects/{project_id}/report   # 最终报告
   ```

2. **数据库**：SQLite WAL 模式，`research_projects` 表

3. **核心模块**：
   - `research_team/models.py` - Pydantic 模型
   - `research_team/database.py` - SQLite ORM
   - `research_team/project_manager.py` - 异步任务管理
   - `research_team/client_safe.py` - 线程安全 Client
   - `app/gateway/routers/research.py` - API 路由

### API 契约详情

> **重要**：所有需要用户身份的 API 端点都需要在请求头中携带 `X-User-ID`。该头由鉴权中间件设置，前端需要从会话中获取并传递。

#### POST /api/research/projects

**Request**:
```json
{
  "topic": "2026年协作机器人发展趋势",
  "directions": ["技术趋势", "市场分析"]
}
```

**Headers**:
```
X-User-ID: user_123
```

**Response 201**:
```json
{
  "project_id": "proj_abc123",
  "status": "pending",
  "created_at": "2026-04-05T10:00:00Z",
  "message": "项目已创建，研究团队正在启动"
}
```

#### GET /api/research/projects

**Headers**:
```
X-User-ID: user_123
```

**Response 200**:
```json
{
  "projects": [
    {
      "project_id": "proj_abc123",
      "topic": "2026年协作机器人发展趋势",
      "status": "in_progress",
      "progress": 40,
      "current_phase": "collecting",
      "created_at": "2026-04-05T10:00:00Z",
      "updated_at": "2026-04-05T10:15:00Z"
    }
  ],
  "total": 1
}
```

#### GET /api/research/projects/{project_id}

**Response 200**:
```json
{
  "project_id": "proj_abc123",
  "topic": "2026年协作机器人发展趋势",
  "directions": ["技术趋势", "市场分析"],
  "status": "in_progress",
  "progress": 40,
  "current_phase": "collecting",
  "error_message": null,
  "created_at": "2026-04-05T10:00:00Z",
  "updated_at": "2026-04-05T10:15:00Z"
}
```

#### GET /api/research/projects/{project_id}/report

**Response 200**:
```json
{
  "project_id": "proj_abc123",
  "report": "# 2026年协作机器人发展趋势\n\n## 执行摘要\n...",
  "format": "markdown",
  "word_count": 12500
}
```

### 状态枚举

**ResearchStatus**:
- `pending` - 待处理
- `in_progress` - 进行中
- `completed` - 已完成
- `failed` - 失败
- `cancelled` - 已取消

**ResearchPhase**:
- `planning` - 制定计划 (10%)
- `collecting` - 信息搜集 (40%)
- `analyzing` - 分析 (60%)
- `writing` - 报告撰写 (80%)
- `reviewing` - 审核 (90%)
- `completed` - 完成 (100%)

---

## 结论

### 已完成

- [x] SQLite 数据库层（WAL 模式）
- [x] Pydantic 模型定义
- [x] 线程安全 DeerFlowClient
- [x] 异步任务管理器
- [x] 6 个 REST API 端点
- [x] API 路由注册到 FastAPI

### 未完成

- [ ] 中间产出 API（`/outputs`）- 返回空数组，需要后续实现
- [ ] 任务取消功能（`DELETE` 端点）- 状态更新未完成
- [ ] 前端 UI

---

## 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| 研究任务耗时长（30min+） | 前端轮询可能超时 | 建议前端设置 30min 超时提示 |
| 中间产出未实现 | 无法查看阶段性成果 | 先开发其他页面，outputs 后续补 |
| 报告仅支持 Markdown | 前端需自行渲染 | 使用 `react-markdown` 或类似库 |

---

## 待确认项

| 项 | 状态 | 说明 |
|----|------|------|
| 用户 ID 如何获取 | 待确认 | 当前 API 需要前端传入 user_id，实际应从会话获取 |
| 轮询间隔 | 建议 30s-60s | 过长体验差，过短服务器压力大 |
| 报告渲染方案 | 待选择 | react-markdown / marked / 其他 |

---

## UI 设计约束

### 目标端

- 主要：Web 浏览器（桌面端优先，1440px+）
- 次要：移动端响应式（375px+）

### 页面清单

| 页面 | 路径 | 说明 |
|------|------|------|
| 研究任务创建 | `/research/new` | 表单：topic + directions |
| 研究列表 | `/research` | 用户项目列表 |
| 研究详情 | `/research/[id]` | 进度 + 中间产出 |
| 报告查看 | `/research/[id]/report` | Markdown 渲染 |

### 设计 Token

建议复用 DeerFlow 现有 UI token（需前端工程师确认）。

### 关键交互

1. **创建任务**：3 步内完成，显示 loading 状态
2. **进度展示**：6 阶段进度条（planning → collecting → analyzing → writing → reviewing → completed）
3. **轮询机制**：每 30s 刷新一次详情页状态
4. **报告查看**：Markdown 渲染 + 复制/下载按钮

---

## 下一跳角色

### frontend-engineer

**期望动作**：
1. 基于 API 契约开发 4 个页面
2. 实现轮询机制（30s 间隔）
3. 实现 Markdown 渲染
4. 自测所有交互路径

**验收标准**：
- [ ] 可在 3 步内创建研究任务
- [ ] 进度实时更新（6 阶段）
- [ ] 报告可在线阅读
- [ ] 响应式（1440/768/375px）

---

## 下游质疑记录

> 接收方必须先留下至少 1 条对上游输入合理性的质疑

| 质疑内容 | 质疑目标 | 结论 |
|---------|---------|------|
| `user_id` 从何获取？当前 API 设计需要前端传入，但实际应用中用户身份应从会话/鉴权层获取 | API 契约（POST /projects, GET /projects） | **已确认**：后端从请求头/会话获取 user_id（`X-User-ID`），前端不传入 |
| 中间产出 API 返回空数组，这个端点的实际数据来源是什么？ | GET /outputs | **已确认**：outputs 数据存储到 DB，设计单独的 outputs 表 |

---

## 决策更新（用户确认）

| 项 | 决策 | 实现方式 |
|----|------|----------|
| user_id 获取 | **鉴权** | 请求头 `X-User-ID`，后端从会话/鉴权中间件获取 |
| outputs 数据源 | **DB** | 新增 `research_outputs` 表存储中间产出 |

---

## 阶段切换凭证

| 检查项 | 状态 |
|--------|------|
| PRD 已完成 | ✅ |
| 需求挑战会已完成 | ✅ |
| Arch Design 已完成 | ✅ |
| Delivery Plan 已完成 | ✅ |
| 后端 API 基础实现已完成 | ✅ |
| 前端尚未开始 | ⚠️ |

**当前状态**：后端基础实现完成，可交接给前端。前端完成后进入 review 阶段。

---

## 附录：可追溯文件

| 文件 | 路径 |
|------|------|
| PRD | `docs/artifacts/2026-04-05-research-team-collaboration/prd.md` |
| Arch Design | `docs/artifacts/2026-04-05-research-team-collaboration/arch-design.md` |
| Delivery Plan | `docs/artifacts/2026-04-05-research-team-collaboration/delivery-plan.md` |
| Execute Log | `docs/artifacts/2026-04-05-research-team-collaboration/execute-log.md` |
