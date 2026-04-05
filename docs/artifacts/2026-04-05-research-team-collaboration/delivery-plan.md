---
artifact: delivery-plan
task: research-team-collaboration
date: 2026-04-05
role: tech-lead
status: draft
---

# 研究团队协作系统 - 交付计划

## 1. 版本目标

### 当前版本 (v1.0)

**范围**：
- 后端：研究任务 API + SQLite 持久化 + 异步任务管理
- 前端：研究任务创建页 + 列表页 + 详情页 + 报告查看器
- 集成：端到端研究任务流程

**放行标准**：
- [ ] 用户可成功创建研究项目（API 验证）
- [ ] 研究团队可完成完整流程并产出报告
- [ ] 前端 UI 可追踪进度和查看报告
- [ ] 多用户数据隔离验证通过
- [ ] 任务取消功能正常

---

## 2. 需求挑战会结论

### 质疑 1: DeerFlowClient 非线程安全

**质疑内容**：`DeerFlowClient` 包含可变共享状态，多线程并发访问会导致竞态条件。

**质疑目标**：现有 `research_team.py` 使用 `ThreadPoolExecutor` 并发调用同一 `DeerFlowClient` 实例。

**结论**：
- 接受原问题
- 替代方案：每个并发任务创建独立 `DeerFlowClient` 实例（线程本地存储）
- 不阻断实施，但需在实现阶段重点验证

### 质疑 2: SQLite 持久化未实现

**质疑内容**：需求文档声称"持久化：SQLite"，但代码中无任何 SQLite 集成。

**质疑目标**：`ResearchProject` 仅为内存 dataclass，进程结束后状态丢失。

**结论**：
- 接受原问题
- 本版本新增 SQLite 持久化层（`database.py`）
- 需设计表结构和迁移策略

### 质疑 3: 同步阻塞模型与 Web UI 不兼容

**质疑内容**：`team.run()` 同步阻塞调用，不支持轮询和任务中断。

**质疑目标**：当前 `run()` 方法直接返回结果，无中间状态。

**结论**：
- 接受原问题
- 本版本改造为 `BackgroundTasks` 异步执行
- 增加进度更新机制（每阶段更新 progress）

### 质疑 4: 审核员角色价值

**质疑内容**：5 角色中"审核员"是否真正必要？是否会拖慢流程？

**质疑目标**：PRD 中定义的角色分工。

**结论**：
- 接受保留审核员
- 审核员可提升报告质量下限
- 可在 v1.1 考虑简化（审核通过则直接输出）

### 替代路径：Subagent vs 独立模块

**讨论结论**：
- 选择：保持 `research_team/` 作为独立模块，不深度耦合到 DeerFlow 主流程
- 理由：解耦清晰，研究团队可独立演进；复用现有 DeerFlowClient 而非改造 LangGraph

---

## 3. 角色分工

| 角色 | 主责 | 协作方 | 交付物 |
|------|------|--------|--------|
| **tech-lead** | 整体把控、方案评审 | 所有角色 | PRD、Delivery Plan、Arch Design |
| **architect** | 系统架构设计 | backend-engineer | arch-design.md |
| **backend-engineer** | 后端 API + 数据库 + 异步任务 | frontend-engineer | research router、database.py、project_manager.py |
| **frontend-engineer** | 前端 UI | backend-engineer | 4 个页面组件 |
| **qa-engineer** | 测试计划、E2E 测试 | backend-engineer | test-plan.md、E2E 测试用例 |

### 交接顺序

```
architect (Arch Design)
    ↓
backend-engineer (API + DB) ←→ frontend-engineer (并行)
    ↓
qa-engineer (测试)
    ↓
tech-lead (评审放行)
```

---

## 4. 工作拆解

### 阶段 1：后端基础设施（Day 1-2）

| 工作项 | 主责 | 依赖 | 计划时间 |
|--------|------|------|----------|
| SQLite ORM 层 (`database.py`) | backend-engineer | 无 | Day 1 |
| Pydantic 模型 (`models.py`) | backend-engineer | 无 | Day 1 |
| 线程安全 Client (`client_safe.py`) | backend-engineer | 无 | Day 1 |
| API 路由骨架 (`routers/research.py`) | backend-engineer | models.py | Day 1-2 |
| 研究团队改造（异步化） | backend-engineer | client_safe.py | Day 2 |

**验收标准**：
- `POST /api/research/projects` 返回 201
- `GET /api/research/projects` 返回项目列表
- `GET /api/research/projects/{id}` 返回项目详情

### 阶段 2：异步任务系统（Day 3-5）

| 工作项 | 主责 | 依赖 | 计划时间 |
|--------|------|------|----------|
| 项目管理器 (`project_manager.py`) | backend-engineer | database.py | Day 3 |
| ResearchTeam 异步改造 | backend-engineer | client_safe.py | Day 3-4 |
| 进度更新机制 | backend-engineer | project_manager.py | Day 4 |
| 任务取消机制 | backend-engineer | project_manager.py | Day 4 |
| 中间产出 API | backend-engineer | project_manager.py | Day 5 |
| 最终报告 API | backend-engineer | project_manager.py | Day 5 |

**验收标准**：
- 后台任务可正常执行（完整跑通 5 阶段）
- 进度可实时查询（每分钟更新）
- 任务可取消
- 报告可生成和获取

### 阶段 3：前端 UI（Day 4-6，与阶段 2 并行）

| 工作项 | 主责 | 依赖 | 计划时间 |
|--------|------|------|----------|
| 研究任务创建页 | frontend-engineer | API 契约 | Day 4-5 |
| 研究列表页 | frontend-engineer | API 契约 | Day 5 |
| 研究详情页 | frontend-engineer | outputs API | Day 5-6 |
| 报告查看器 | frontend-engineer | report API | Day 6 |

**验收标准**：
- 3 步内完成研究任务创建
- 进度实时显示（每分钟刷新）
- 报告可在线阅读和下载

### 阶段 4：测试与收尾（Day 7）

| 工作项 | 主责 | 依赖 | 计划时间 |
|--------|------|------|----------|
| 单元测试 | backend-engineer | 所有后端代码 | Day 7 |
| E2E 测试 | qa-engineer | 前后端完成 | Day 7 |
| 文档更新 | tech-lead | 所有交付物 | Day 7 |

**验收标准**：
- 单元测试覆盖率 ≥ 70%
- E2E 测试覆盖主路径
- CLAUDE.md 已更新

---

## 5. 风险与缓解

| 风险 | 等级 | 影响 | 缓解措施 | Owner |
|------|------|------|----------|-------|
| DeerFlowClient 线程安全 | **高** | 多线程并发不稳定 | 每个任务独立实例 + 压力测试 | backend-engineer |
| SQLite 并发写入冲突 | 中 | 高并发下请求失败 | WAL 模式 + 连接池 + 重试机制 | backend-engineer |
| 长任务超时 | 中 | 用户体验差 | 心跳机制 + 前端超时提示 + 任务恢复 | backend-engineer |
| 前端 API 对接延迟 | 低 | 进度阻塞 | API 契约提前评审 + Mock 测试 | frontend-engineer |
| 报告质量不稳定 | 中 | 用户满意度低 | 审核员角色保留 + 质量门禁 | backend-engineer |

---

## 6. 节点检查

| 节点 | 时间 | 检查内容 | 放行标准 |
|------|------|----------|----------|
| **方案评审** | Day 1 | Arch Design 评审 | 所有角色无异议 |
| **后端完成** | Day 5 | API + DB + 异步任务 | 单元测试通过 |
| **前端完成** | Day 6 | 4 个页面完成 | 页面可操作，无明显 bug |
| **测试完成** | Day 7 | E2E 测试 | 主路径 100% 通过 |
| **发布准备** | Day 7 | 代码 Review + 文档 | tech-lead 放行 |

---

## 7. 技能装配清单

### shared skills（必须）

| Skill | 用途 | 启用原因 |
|-------|------|----------|
| `frontend-engineering` | 前端组件规范 | 涉及 Web UI 开发 |
| `frontend-ui-ux-system` | 设计 token + 交互 | 涉及 UI/UX 交付 |

### ecc skills（按需）

| Skill | 用途 | 启用原因 |
|-------|------|----------|
| `python-patterns` | Python 最佳实践 | 后端开发 |
| `fastapi-patterns` | FastAPI 设计 | API 开发 |
| `database-reviewer` | SQLite 评审 | 数据库设计 |

### company skills

无（本次不涉及海尔特定场景）

---

## 8. 前端交付物与检查点

### UI 交付物

| 页面 | 路径 | 组件 |
|------|------|------|
| 研究任务创建 | `/research/new` | ResearchCreateForm |
| 研究列表 | `/research` | ResearchList, ResearchCard |
| 研究详情 | `/research/{id}` | ResearchDetail, ProgressTimeline, OutputPanel |
| 报告查看 | `/research/{id}/report` | ReportViewer, MarkdownRenderer |

### 质量检查点

| 检查项 | 标准 | 工具 |
|--------|------|------|
| 响应式 | 1440/768/375px 三断点 | 浏览器 DevTools |
| 可访问性 | 键盘导航 + 屏幕阅读器 | axe-core |
| 性能 | 首屏 <2s，API <500ms | Lighthouse |
| 错误处理 | 所有异常有提示 | 人工测试 |

---

## 9. 应用等级与技术架构等级

### 应用等级

| 维度 | 评估 | 依据 |
|------|------|------|
| 业务评定等级 | **T4** | 辅助研究工具，不涉及核心业务 |
| 技术架构等级 | **T4** | 单体部署，无高可用要求 |
| 数据敏感度 | **低** | 研究公开信息，无 PII |

### 关键组件偏离

| 组件 | 偏离情况 | 说明 |
|------|----------|------|
| SQLite | 无偏离 | T4 允许使用，无需 PostgreSQL |
| 本地存储 | 无偏离 | 单机部署适合 |
| 无消息队列 | 无偏离 | FastAPI BackgroundTasks 足够 |

### ADR 要求

无需 ADR（本版本无架构级决策变更，方案已在 arch-design.md 中明确）

---

## 10. 升级点与检查机制

### 升级触发条件

| 场景 | 升级到 |
|------|--------|
| 架构方案有分歧 | tech-lead 仲裁 |
| 进度延迟 > 1 天 | project-manager 协调 |
| 发现关键技术风险 | tech-lead + architect |

### 日常检查

- 每日站会（异步）：各角色报告进度和阻塞
- 阻塞项第一时间在群内升级

---

## 11. 附录：API 契约（供前端对接）

### 接口清单

```
POST   /api/research/projects          # 创建项目
GET    /api/research/projects           # 列表（需 user_id 参数）
GET    /api/research/projects/{id}     # 详情
DELETE /api/research/projects/{id}     # 取消
GET    /api/research/projects/{id}/outputs  # 中间产出
GET    /api/research/projects/{id}/report   # 最终报告
```

详见 `arch-design.md` 第 4 节。
