"""
Client 导入兼容层

DeerFlow 的 Python Client 类名为 DeerFlowClient，
这个文件提供便捷导入并兼容 ResearchTeam 的写法。
"""
import sys
from pathlib import Path

# 确保 deerflow 包在路径中
_backend = Path(__file__).parent.parent / "backend"  # noqa: E402
if not any(str(_backend) in p for p in sys.path):
    sys.path.insert(0, str(_backend))  # noqa: E402

from packages.harness.deerflow.client import DeerFlowClient  # noqa: E402

# 方便研究团队直接 from research_team import DeerFlowClient
DeerFlow = DeerFlowClient

__all__ = ["DeerFlowClient", "DeerFlow"]
