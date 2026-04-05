"""
研究团队 - FastAPI 路由

提供研究项目的 REST API 端点

用户身份通过 X-User-ID 请求头获取（由鉴权中间件设置）
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException

from research_team.database import get_outputs_by_project, get_project, get_projects_by_user, update_project
from research_team.models import (
    CancelProjectResponse,
    CreateProjectRequest,
    CreateProjectResponse,
    ErrorResponse,
    PhaseOutput,
    PhaseOutputsResponse,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectSummary,
    ReportResponse,
)
from research_team.project_manager import ProjectManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])


# ============================================================================
# 全局管理器（单例）
# ============================================================================

_manager: ProjectManager | None = None


def get_manager() -> ProjectManager:
    """获取项目管理器单例"""
    global _manager
    if _manager is None:
        _manager = ProjectManager()
    return _manager


# ============================================================================
# 辅助函数
# ============================================================================

def _get_user_id(x_user_id: str | None = Header(None)) -> str:
    """从请求头获取用户 ID"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-ID header")
    return x_user_id


async def _run_research_task(
    project_id: str,
    topic: str,
    directions: list[str],
    user_id: str,
) -> None:
    """后台执行研究任务"""
    try:
        manager = get_manager()
        executor = await manager.start_research(
            project_id=project_id,
            topic=topic,
            directions=directions,
            user_id=user_id,
        )
        await executor.run()
    except Exception as e:
        logger.exception(f"Research task failed for project {project_id}: {e}")
        # 错误已通过 update_project 记录到数据库


# ============================================================================
# API 端点
# ============================================================================


@router.post(
    "/projects",
    response_model=CreateProjectResponse,
    status_code=201,
    responses={400: {"model": ErrorResponse}},
)
async def create_project(
    request: CreateProjectRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> CreateProjectResponse:
    """
    创建新的研究项目

    创建项目后，研究团队会自动开始执行研究任务。
    用户ID从 X-User-ID 请求头获取（由鉴权中间件设置）。
    """
    try:
        manager = get_manager()
        entity = await manager.create_project(
            topic=request.topic,
            directions=request.directions,
            user_id=x_user_id,
        )

        # 启动后台任务
        import asyncio
        asyncio.create_task(
            _run_research_task(
                entity.project_id,
                entity.topic,
                entity.directions,
                entity.user_id,
            )
        )

        return CreateProjectResponse(
            project_id=entity.project_id,
            status=entity.status,
            created_at=entity.created_at,
            message="项目已创建，研究团队正在启动",
        )

    except Exception as e:
        logger.exception(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/projects",
    response_model=ProjectListResponse,
)
async def list_projects(
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> ProjectListResponse:
    """
    获取用户的所有研究项目列表

    用户ID从 X-User-ID 请求头获取（由鉴权中间件设置）。
    """
    try:
        entities = await get_projects_by_user(x_user_id)
        summaries = [
            ProjectSummary(
                project_id=e.project_id,
                topic=e.topic,
                status=e.status,
                progress=e.progress,
                current_phase=e.current_phase,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
            for e in entities
        ]
        return ProjectListResponse(projects=summaries, total=len(summaries))

    except Exception as e:
        logger.exception(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/projects/{project_id}",
    response_model=ProjectDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_project_detail(project_id: str) -> ProjectDetailResponse:
    """
    获取研究项目详情
    """
    entity = await get_project(project_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectDetailResponse(
        project_id=entity.project_id,
        topic=entity.topic,
        directions=entity.directions,
        status=entity.status,
        progress=entity.progress,
        current_phase=entity.current_phase,
        error_message=entity.error_message,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.delete(
    "/projects/{project_id}",
    response_model=CancelProjectResponse,
    responses={404: {"model": ErrorResponse}},
)
async def cancel_project(project_id: str) -> CancelProjectResponse:
    """
    取消研究项目

    注意：仅能取消处于 PENDING 或 IN_PROGRESS 状态的项目
    """
    entity = await get_project(project_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if entity.status.value not in ("pending", "in_progress"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel project in status: {entity.status.value}",
        )

    from research_team.models import ResearchStatus
    await update_project(project_id, status=ResearchStatus.CANCELLED)

    return CancelProjectResponse(
        project_id=project_id,
        status=ResearchStatus.CANCELLED,
        message="项目已取消",
    )


@router.get(
    "/projects/{project_id}/outputs",
    response_model=PhaseOutputsResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_project_outputs(project_id: str) -> PhaseOutputsResponse:
    """
    获取研究项目的中间产出

    从数据库读取所有阶段产出。
    """
    entity = await get_project(project_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Project not found")

    outputs = await get_outputs_by_project(project_id)
    phase_outputs = [
        PhaseOutput(
            phase=o.phase,
            direction=o.direction,
            content=o.content,
            created_at=o.created_at,
        )
        for o in outputs
    ]

    return PhaseOutputsResponse(
        project_id=project_id,
        outputs=phase_outputs,
    )


@router.get(
    "/projects/{project_id}/report",
    response_model=ReportResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_project_report(project_id: str) -> ReportResponse:
    """
    获取研究项目的最终报告
    """
    entity = await get_project(project_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if entity.final_report_path:
        report_path = Path(entity.final_report_path)
        if report_path.exists():
            report = report_path.read_text(encoding="utf-8")
            word_count = len(report)
            return ReportResponse(
                project_id=project_id,
                report=report,
                format="markdown",
                word_count=word_count,
            )

    if entity.status.value == "failed":
        return ReportResponse(
            project_id=project_id,
            report=None,
            message=f"研究失败: {entity.error_message}",
        )

    if entity.status.value in ("pending", "in_progress"):
        return ReportResponse(
            project_id=project_id,
            report=None,
            message="研究尚未完成",
        )

    return ReportResponse(
        project_id=project_id,
        report=None,
        message="报告不存在",
    )
