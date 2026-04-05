---
name: research-team-collaboration
description: 研究团队协作系统 - 用户发布任务后多Agent协作完成研究
type: project
---

# 项目上下文

## 项目信息

| 字段 | 值 |
|------|-----|
| 项目名 | 研究团队协作系统 (Research Team Collaboration) |
| Task Slug | research-team-collaboration |
| 开始日期 | 2026-04-05 |
| 状态 | 规划阶段 |

## Tech Stack

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12+, FastAPI, aiosqlite |
| Agent 框架 | DeerFlow (LangGraph-based) |
| 前端 | Next.js 16 + React 19 + TypeScript |
| 持久化 | SQLite (WAL 模式) |
| 任务队列 | FastAPI BackgroundTasks |

## 当前任务

**目标**：实现用户发布研究任务 → 系统自动组建研究团队 → 多 Agent 协作完成 → 用户获取研究报告

**关键约束**（已确认）：
- 持久化：SQLite
- 多用户隔离：需要（按 user_id）
- 通知机制：轮询
- 报告存储：本地 `backend/research_outputs/`

## 关键依赖

| 依赖 | 状态 | 说明 |
|------|------|------|
| `backend/research_team/` | 已有 | 5 角色 Agent + ResearchTeam 编排器 |
| `DeerFlowClient` | 已有 | 需改造为线程安全 |
| `deep-research skill` | 已有 | 可直接复用 |
| `skills/public/deep-research/` | 已有 | 研究方法论 |

## 活跃风险

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| DeerFlowClient 线程安全 | **高** | 每个任务独立实例（线程本地存储） |
| SQLite 并发写入 | 中 | WAL 模式 + busy_timeout |
| 长任务超时 | 中 | 心跳机制 + 进度更新 |

## 实施路线图

1. **Day 1-2**：后端基础设施（database.py, models.py, router）
2. **Day 3-5**：异步任务系统（project_manager, ResearchTeam 改造）
3. **Day 4-6**：前端 UI（并行）
4. **Day 7**：测试与收尾

## 产出物

| 文档 | 路径 |
|------|------|
| PRD | `docs/artifacts/2026-04-05-research-team-collaboration/prd.md` |
| Arch Design | `docs/artifacts/2026-04-05-research-team-collaboration/arch-design.md` |
| Delivery Plan | `docs/artifacts/2026-04-05-research-team-collaboration/delivery-plan.md` |

## 下一步

进入 `/team-execute` 阶段，由 backend-engineer 和 frontend-engineer 协作实现。
