"""
研究团队 - 线程安全 DeerFlowClient 包装

问题：DeerFlowClient 非线程安全，同一实例被多线程并发访问会导致竞态条件
方案：为每个并发任务创建独立 DeerFlowClient 实例（线程本地存储）
"""

import sys
import threading
from pathlib import Path

# 确保 deerflow 包在路径中
_backend = Path(__file__).parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from packages.harness.deerflow.client import DeerFlowClient  # noqa: E402

# ============================================================================
# 线程本地存储
# ============================================================================

_thread_local = threading.local()


# ============================================================================
# 线程安全 Client 管理
# ============================================================================


def get_client(
    model_name: str = "minimax-m2.7-highspeed",
    thinking_enabled: bool = True,
    subagent_enabled: bool = True,
) -> DeerFlowClient:
    """
    获取当前线程独立的 DeerFlowClient 实例

    每个调用线程第一次调用时会创建新实例，
    后续调用复用同一实例。

    Args:
        model_name: 模型名称
        thinking_enabled: 是否启用思维链
        subagent_enabled: 是否启用子代理

    Returns:
        当前线程独立的 DeerFlowClient 实例
    """
    if not hasattr(_thread_local, "client"):
        _thread_local.client = DeerFlowClient(
            model_name=model_name,
            thinking_enabled=thinking_enabled,
            subagent_enabled=subagent_enabled,
        )
    return _thread_local.client


def clear_thread_client() -> None:
    """清除当前线程的 client 实例（用于资源清理）"""
    if hasattr(_thread_local, "client"):
        del _thread_local.client


# ============================================================================
# 上下文管理器（用于显式管理 client 生命周期）
# ============================================================================


class ThreadSafeClient:
    """
    线程安全 DeerFlowClient 上下文管理器

    使用方式：
        with ThreadSafeClient() as client:
            response = client.chat(message, thread_id=thread_id)

    或直接获取：
        client = get_client()
    """

    def __init__(
        self,
        model_name: str = "minimax-m2.7-highspeed",
        thinking_enabled: bool = True,
        subagent_enabled: bool = True,
    ):
        self.model_name = model_name
        self.thinking_enabled = thinking_enabled
        self.subagent_enabled = subagent_enabled
        self._client: DeerFlowClient | None = None

    def __enter__(self) -> DeerFlowClient:
        """进入上下文，返回线程安全的 client"""
        self._client = get_client(
            model_name=self.model_name,
            thinking_enabled=self.thinking_enabled,
            subagent_enabled=self.subagent_enabled,
        )
        return self._client

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文，不关闭 client（因为是线程共享）"""
        # 不清理 client，因为它是线程共享的
        pass
