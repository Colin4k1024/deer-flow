"""
深度研究团队（Deep Research Team）for DeerFlow

提供自定义角色 Agent 和团队编排器，用于深度研究任务。

使用示例：

1. 使用 DeerFlow Python Client 直接调用：

```python
from packages.harness.deerflow.client import DeerFlowClient

client = DeerFlowClient(
    model_name="minimax-m2.7-highspeed",
    thinking_enabled=True,
    subagent_enabled=True,
)

# 首席研究员
response = client.chat("研究协作机器人的最新进展", thread_id="research-1")

# 信息搜集员
response = client.chat(
    "请搜集协作机器人相关的最新资料，使用 deep-research skill",
    thread_id="research-1"
)
```

2. 使用团队编排器（研究团队）：

```python
from research_team import ResearchTeam

team = ResearchTeam(
    topic="前沿制造最新进展",
    directions=["协作机器人", "智能工厂", "3D打印"],
)

project = team.run()
print(project.final_report)
```

3. 创建自定义角色 Agent：

```python
from research_team.agents import ROLE_AGENTS, INFORMATION_COLLECTOR_PROMPT
from deerflow.agents.factory import create_deerflow_agent
from deerflow.models import create_chat_model

model = create_chat_model(name="minimax-m2.7-highspeed")
agent = create_deerflow_agent(
    model=model,
    system_prompt=INFORMATION_COLLECTOR_PROMPT,
)
```
"""

from .agents import ROLE_AGENTS
from .client_patch import DeerFlowClient
from .database import delete_project, get_project, get_projects_by_user, update_project
from .models import (
    CancelProjectResponse,
    CreateProjectRequest,
    CreateProjectResponse,
    ErrorResponse,
    PhaseOutputsResponse,
    ProjectDetailResponse,
    ProjectListResponse,
    ReportResponse,
    ResearchPhase,
)
from .project_manager import AsyncResearchTeam, ProjectManager
from .research_team import ResearchProject, ResearchStatus, ResearchTeam

__all__ = [
    # 原有导出
    "ResearchTeam",
    "ResearchStatus",
    "ResearchProject",
    "ROLE_AGENTS",
    "DeerFlowClient",
    # 新增导出
    "ResearchPhase",
    "CreateProjectRequest",
    "CreateProjectResponse",
    "ProjectListResponse",
    "ProjectDetailResponse",
    "CancelProjectResponse",
    "PhaseOutputsResponse",
    "ReportResponse",
    "ErrorResponse",
    "get_project",
    "get_projects_by_user",
    "update_project",
    "delete_project",
    "ProjectManager",
    "AsyncResearchTeam",
]
