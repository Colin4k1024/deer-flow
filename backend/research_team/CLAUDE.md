# 深度研究团队 - DeerFlow Agent 代码

## 文件结构

```
backend/research_team/
├── __init__.py                 # 包入口，导出 ResearchTeam 和 ROLE_AGENTS
├── research_team.py            # 团队编排器（ResearchTeam 类）
├── client_patch.py             # DeerFlowClient 兼容导入层
├── run_research.py             # 命令行启动脚本
├── agents/                     # 角色 Agent 定义
│   ├── __init__.py            # 导出所有角色
│   ├── lead_researcher.py     # 首席研究员 prompt
│   ├── information_collector.py # 信息搜集员 prompt
│   ├── analyst.py              # 分析师 prompt
│   ├── report_writer.py        # 报告撰写员 prompt
│   └── reviewer.py             # 审核员 prompt
└── skills/
    └── deep-research/
        └── SKILL.md            # 前沿制造领域专用 deep-research skill
```

## 快速使用

```bash
cd ~/Desktop/poc/deer-flow/backend

# 交互模式
uv run python -m research_team.run_research --interactive

# 直接运行
uv run python -m research_team.run_research \
  --topic "协作机器人最新进展" \
  --directions "技术趋势" "市场分析" "应用案例"
```

## Python API

```python
from research_team import ResearchTeam

team = ResearchTeam(
    topic="前沿制造最新进展",
    directions=["协作机器人", "智能工厂", "3D打印"],
    model_name="minimax-m2.7-highspeed",
)
project = team.run()
print(project.final_report)
```

## 角色 Agent 单独使用

```python
from research_team.agents import ROLE_AGENTS

# 获取某个角色的 prompt
print(ROLE_AGENTS["information_collector"]["prompt"])

# 创建自定义 DeerFlow Agent
from research_team.agents import INFORMATION_COLLECTOR_PROMPT
from deerflow.agents.factory import create_deerflow_agent
from deerflow.models import create_chat_model

model = create_chat_model(name="minimax-m2.7-highspeed")
agent = create_deerflow_agent(
    model=model,
    system_prompt=INFORMATION_COLLECTOR_PROMPT,
)
```

## 团队工作流程

```
1. 首席研究员制定研究计划
      ↓
2. 并行：信息搜集员 × N 个方向
      ↓
3. 并行：分析师 × N 个方向
      ↓
4. 报告撰写员整合 + 审核员审核
      ↓
5. 最终报告
```

## 依赖

- DeerFlow Python 包（`packages.harness.deerflow`）
- `DeerFlowClient` from `packages.harness.deerflow.client`
- Python 3.12+
