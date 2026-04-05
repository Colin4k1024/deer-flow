"""
研究团队 - Pydantic 模型和 dataclass 实体

定义 API 请求/响应模型和数据库实体模型
"""

import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# 确保 deerflow 包在路径中
_backend = Path(__file__).parent.parent / "backend"  # noqa: E402
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))  # noqa: E402


# ============================================================================
# Enums
# ============================================================================

class ResearchStatus(str, Enum):
    """研究项目状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchPhase(str, Enum):
    """研究阶段"""
    PLANNING = "planning"           # 制定计划
    COLLECTING = "collecting"       # 信息搜集
    ANALYZING = "analyzing"         # 分析
    WRITING = "writing"             # 报告撰写
    REVIEWING = "reviewing"         # 审核
    COMPLETED = "completed"         # 完成


# ============================================================================
# Pydantic Models (API 层)
# ============================================================================

from pydantic import BaseModel, Field  # noqa: E402


class CreateProjectRequest(BaseModel):
    """创建研究项目请求

    注意：user_id 从 X-User-ID 请求头获取，不在此处传入
    """
    topic: str = Field(..., min_length=1, max_length=500, description="研究课题")
    directions: list[str] = Field(default_factory=list, max_length=5, description="研究方向")


class CreateProjectResponse(BaseModel):
    """创建研究项目响应"""
    project_id: str
    status: ResearchStatus
    created_at: str
    message: str = "项目已创建，研究团队正在启动"


class ProjectSummary(BaseModel):
    """项目摘要（列表用）"""
    project_id: str
    topic: str
    status: ResearchStatus
    progress: int = Field(ge=0, le=100)
    current_phase: ResearchPhase | None = None
    created_at: str
    updated_at: str


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    projects: list[ProjectSummary]
    total: int


class ProjectDetailResponse(BaseModel):
    """项目详情响应"""
    project_id: str
    topic: str
    directions: list[str]
    status: ResearchStatus
    progress: int = Field(ge=0, le=100)
    current_phase: ResearchPhase | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str


class CancelProjectResponse(BaseModel):
    """取消项目响应"""
    project_id: str
    status: ResearchStatus
    message: str


class PhaseOutput(BaseModel):
    """阶段产出"""
    phase: ResearchPhase
    direction: str | None = None
    content: str
    created_at: str


class PhaseOutputsResponse(BaseModel):
    """中间产出响应"""
    project_id: str
    outputs: list[PhaseOutput]


class ReportResponse(BaseModel):
    """最终报告响应"""
    project_id: str
    report: str | None = None
    format: str = "markdown"
    word_count: int | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    """错误响应"""
    error_code: str
    message: str
    detail: str | None = None


# ============================================================================
# Dataclass Entities (数据库层)
# ============================================================================


@dataclass
class ResearchProjectEntity:
    """研究项目实体"""
    project_id: str
    user_id: str
    topic: str
    directions: list[str]  # JSON string in DB, list in memory
    status: ResearchStatus
    progress: int = 0
    current_phase: ResearchPhase | None = None
    final_report_path: str | None = None
    error_message: str | None = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（用于数据库插入）"""
        return {
            "project_id": self.project_id,
            "user_id": self.user_id,
            "topic": self.topic,
            "directions": json.dumps(self.directions, ensure_ascii=False),
            "status": self.status.value if isinstance(self.status, ResearchPhase) else self.status,
            "progress": self.progress,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "final_report_path": self.final_report_path,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "ResearchProjectEntity":
        """从数据库行创建实体"""
        (
            project_id, user_id, topic, directions, status,
            progress, current_phase, final_report_path, error_message,
            created_at, updated_at
        ) = row
        return cls(
            project_id=project_id,
            user_id=user_id,
            topic=topic,
            directions=json.loads(directions) if directions else [],
            status=ResearchStatus(status),
            progress=progress,
            current_phase=ResearchPhase(current_phase) if current_phase else None,
            final_report_path=final_report_path,
            error_message=error_message,
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class ResearchOutputEntity:
    """研究阶段产出实体"""
    output_id: str
    project_id: str
    phase: ResearchPhase
    direction: str | None
    content: str
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（用于数据库插入）"""
        return {
            "output_id": self.output_id,
            "project_id": self.project_id,
            "phase": self.phase.value,
            "direction": self.direction,
            "content": self.content,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "ResearchOutputEntity":
        """从数据库行创建实体"""
        output_id, project_id, phase, direction, content, created_at = row
        return cls(
            output_id=output_id,
            project_id=project_id,
            phase=ResearchPhase(phase),
            direction=direction,
            content=content,
            created_at=created_at,
        )


# ============================================================================
# 进度映射
# ============================================================================

# 阶段到进度的映射
PHASE_TO_PROGRESS = {
    ResearchPhase.PLANNING: 10,
    ResearchPhase.COLLECTING: 40,
    ResearchPhase.ANALYZING: 60,
    ResearchPhase.WRITING: 80,
    ResearchPhase.REVIEWING: 90,
    ResearchPhase.COMPLETED: 100,
}

# 阶段显示名称
PHASE_DISPLAY_NAMES = {
    ResearchPhase.PLANNING: "制定计划",
    ResearchPhase.COLLECTING: "信息搜集",
    ResearchPhase.ANALYZING: "深度分析",
    ResearchPhase.WRITING: "报告撰写",
    ResearchPhase.REVIEWING: "审核中",
    ResearchPhase.COMPLETED: "已完成",
}
