"""
研究团队 - SQLite 数据库层

使用 aiosqlite 实现异步数据库操作，WAL 模式提升并发性能
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import aiosqlite

# 确保 deerflow 包在路径中
_backend = Path(__file__).parent.parent / "backend"  # noqa: E402
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))  # noqa: E402

from .models import ResearchOutputEntity, ResearchPhase, ResearchProjectEntity, ResearchStatus  # noqa: E402

# ============================================================================
# 配置
# ============================================================================

DB_PATH = Path(__file__).parent.parent / "research_team.db"
BUSY_TIMEOUT_MS = 30000  # 30秒
CONNECTION_POOL_SIZE = 5


# ============================================================================
# 数据库初始化
# ============================================================================

INIT_SQL = """
CREATE TABLE IF NOT EXISTS research_projects (
    project_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    directions TEXT NOT NULL,           -- JSON 数组
    status TEXT NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    current_phase TEXT,
    final_report_path TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON research_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON research_projects(status);

CREATE TABLE IF NOT EXISTS research_outputs (
    output_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    direction TEXT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES research_projects(project_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_outputs_project_id ON research_outputs(project_id);
"""


async def init_db() -> aiosqlite.Connection:
    """初始化数据库连接（设置 WAL 模式和 busy_timeout）"""
    conn = await aiosqlite.connect(DB_PATH, isolation_level=None)
    conn.row_factory = aiosqlite.Row

    # 启用 WAL 模式，提升并发读性能
    await conn.execute("PRAGMA journal_mode=WAL")
    # 设置 busy_timeout，避免写入冲突
    await conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")

    # 创建表
    await conn.executescript(INIT_SQL)
    await conn.commit()

    return conn


# ============================================================================
# 数据库连接管理
# ============================================================================

_db_conn: aiosqlite.Connection | None = None
_lock = asyncio.Lock()


async def get_db() -> aiosqlite.Connection:
    """获取数据库连接（单例模式）"""
    global _db_conn
    async with _lock:
        if _db_conn is None:
            _db_conn = await init_db()
        return _db_conn


async def close_db():
    """关闭数据库连接"""
    global _db_conn
    async with _lock:
        if _db_conn is not None:
            await _db_conn.close()
            _db_conn = None


# ============================================================================
# CRUD 操作
# ============================================================================


async def create_project(entity: ResearchProjectEntity) -> None:
    """创建新项目"""
    db = await get_db()
    now = datetime.utcnow().isoformat() + "Z"
    entity.created_at = now
    entity.updated_at = now

    await db.execute(
        """
        INSERT INTO research_projects
        (project_id, user_id, topic, directions, status, progress,
         current_phase, final_report_path, error_message, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entity.project_id,
            entity.user_id,
            entity.topic,
            json.dumps(entity.directions, ensure_ascii=False),
            entity.status.value,
            entity.progress,
            entity.current_phase.value if entity.current_phase else None,
            entity.final_report_path,
            entity.error_message,
            entity.created_at,
            entity.updated_at,
        ),
    )
    await db.commit()


async def get_project(project_id: str) -> ResearchProjectEntity | None:
    """根据 ID 获取项目"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM research_projects WHERE project_id = ?",
        (project_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return ResearchProjectEntity.from_row(tuple(row))


async def get_projects_by_user(user_id: str) -> list[ResearchProjectEntity]:
    """获取用户的所有项目"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM research_projects WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = await cursor.fetchall()
    return [ResearchProjectEntity.from_row(tuple(row)) for row in rows]


async def update_project(
    project_id: str,
    status: ResearchStatus | None = None,
    progress: int | None = None,
    current_phase: ResearchPhase | None = None,
    final_report_path: str | None = None,
    error_message: str | None = None,
) -> None:
    """更新项目状态和进度"""
    db = await get_db()
    now = datetime.utcnow().isoformat() + "Z"

    updates = []
    params = []

    if status is not None:
        updates.append("status = ?")
        params.append(status.value)
    if progress is not None:
        updates.append("progress = ?")
        params.append(progress)
    if current_phase is not None:
        updates.append("current_phase = ?")
        params.append(current_phase.value)
    if final_report_path is not None:
        updates.append("final_report_path = ?")
        params.append(final_report_path)
    if error_message is not None:
        updates.append("error_message = ?")
        params.append(error_message)

    if updates:
        updates.append("updated_at = ?")
        params.append(now)
        params.append(project_id)

        await db.execute(
            f"UPDATE research_projects SET {', '.join(updates)} WHERE project_id = ?",
            params,
        )
        await db.commit()


async def delete_project(project_id: str) -> bool:
    """删除项目"""
    db = await get_db()
    cursor = await db.execute(
        "DELETE FROM research_projects WHERE project_id = ?",
        (project_id,),
    )
    await db.commit()
    return cursor.rowcount > 0


async def count_projects_by_user(user_id: str) -> int:
    """统计用户项目数量"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM research_projects WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    return row[0] if row else 0


# ============================================================================
# Outputs CRUD
# ============================================================================


async def create_output(entity: ResearchOutputEntity) -> None:
    """创建阶段产出"""
    db = await get_db()
    now = datetime.utcnow().isoformat() + "Z"
    entity.created_at = now

    await db.execute(
        """
        INSERT INTO research_outputs
        (output_id, project_id, phase, direction, content, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            entity.output_id,
            entity.project_id,
            entity.phase.value,
            entity.direction,
            entity.content,
            entity.created_at,
        ),
    )
    await db.commit()


async def get_outputs_by_project(project_id: str) -> list[ResearchOutputEntity]:
    """获取项目的所有阶段产出"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM research_outputs WHERE project_id = ? ORDER BY created_at",
        (project_id,),
    )
    rows = await cursor.fetchall()
    return [ResearchOutputEntity.from_row(tuple(row)) for row in rows]


async def delete_outputs_by_project(project_id: str) -> int:
    """删除项目的所有产出"""
    db = await get_db()
    cursor = await db.execute(
        "DELETE FROM research_outputs WHERE project_id = ?",
        (project_id,),
    )
    await db.commit()
    return cursor.rowcount
