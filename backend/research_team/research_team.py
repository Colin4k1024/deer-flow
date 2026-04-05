"""
深度研究团队（Research Team）编排器
使用 DeerFlow Client 管理多 Agent 协作
"""

import sys
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# 确保 deerflow 包在路径中
_backend = Path(__file__).parent.parent / "backend"  # noqa: E402
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))  # noqa: E402

from packages.harness.deerflow.client import DeerFlowClient  # noqa: E402


class ResearchStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskResult:
    task_id: str
    role: str
    status: ResearchStatus
    output: str | None = None
    error: str | None = None


@dataclass
class ResearchProject:
    project_id: str
    topic: str
    status: ResearchStatus = ResearchStatus.PENDING
    tasks: dict[str, TaskResult] = field(default_factory=dict)
    final_report: str | None = None
    thread_id: str | None = None


class ResearchTeam:
    """
    深度研究团队编排器

    使用 DeerFlow 内置的 DeerFlowClient 创建和管理多个研究角色 Agent，
    协调信息搜集、分析、报告撰写和审核的完整流程。

    使用示例：
        team = ResearchTeam(
            topic="协作机器人最新进展",
            directions=["技术趋势", "市场分析", "应用案例"]
        )
        team.run()
        print(team.get_final_report())
    """

    def __init__(
        self,
        topic: str,
        directions: list[str] | None = None,
        model_name: str = "minimax-m2.7-highspeed",
        output_dir: str = "./research_outputs",
    ):
        self.topic = topic
        self.directions = directions or []
        self.model_name = model_name
        self.output_dir = output_dir

        self.project_id = str(uuid.uuid4())[:8]
        self.client = DeerFlowClient(
            model_name=model_name,
            thinking_enabled=True,
            subagent_enabled=True,
        )
        self.thread_id = str(uuid.uuid4())

        self.project = ResearchProject(
            project_id=self.project_id,
            topic=topic,
            thread_id=self.thread_id,
        )

    def run(self) -> ResearchProject:
        """执行完整的研究流程"""
        self.project.status = ResearchStatus.IN_PROGRESS

        try:
            # 阶段1：首席研究员制定计划
            self._lead_researcher_plan()

            # 阶段2：并行信息搜集（每个 direction 一个搜集任务）
            collection_results = self._parallel_collection(self.directions)

            # 阶段3：并行分析
            analysis_results = self._parallel_analysis(collection_results)

            # 阶段4：报告撰写与审核
            final_report = self._write_and_review(analysis_results)

            self.project.final_report = final_report
            self.project.status = ResearchStatus.COMPLETED

        except Exception as e:
            self.project.status = ResearchStatus.FAILED
            raise e

        return self.project

    def _lead_researcher_plan(self) -> dict[str, Any]:
        """首席研究员：制定研究计划"""
        prompt = f"""作为首席研究员，为以下研究课题制定详细研究计划：

课题：{self.topic}
研究方向：{', '.join(self.directions) if self.directions else '综合研究'}

请输出：
1. 具体研究范围和边界
2. 关键研究问题（3-5个）
3. 研究任务分解（列出每个研究方向的具体任务）
4. 预期产出

请用中文输出。"""

        response = self.client.chat(
            message=prompt,
            thread_id=self.thread_id,
        )

        return {"plan": response}

    def _parallel_collection(self, directions: list[str]) -> dict[str, str]:
        """并行信息搜集"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {}

        def collect_single(topic: str, direction: str) -> tuple[str, str]:
            prompt = f"""作为信息搜集员，深入研究以下课题：

课题：{topic}
方向：{direction}

请严格按照 deep-research skill 执行：
1. 广泛搜索 - 从多个角度搜索相关信息
2. 深度爬取 - 获取重要网页的完整内容
3. 整理汇编 - 按主题分类整理所有资料

输出：结构化的资料汇编，包含标题、链接、摘要、来源。

请用中文输出。"""

            result = self.client.chat(
                message=prompt,
                thread_id=self.thread_id + f"-{direction}",
            )
            return direction, result

        with ThreadPoolExecutor(max_workers=len(self.directions)) as executor:
            futures = {
                executor.submit(collect_single, self.topic, d): d
                for d in self.directions
            }
            for future in as_completed(futures):
                direction = futures[future]
                try:
                    results[direction] = future.result()[1]
                except Exception as e:
                    results[direction] = f"Error: {str(e)}"

        return results

    def _parallel_analysis(self, collection_results: dict[str, str]) -> dict[str, str]:
        """并行分析"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {}

        def analyze_single(direction: str, data: str) -> tuple[str, str]:
            prompt = f"""作为分析师，对以下研究资料进行深度分析：

研究方向：{direction}
资料：{data}

请输出：
1. 核心技术发现
2. 市场与产业动态
3. 关键洞察（5-8个），每个洞察需包含：观点、证据、数据来源
4. 趋势预测（短期1-2年，中期3-5年）
5. 初步结论

请用中文输出。"""

            result = self.client.chat(
                message=prompt,
                thread_id=self.thread_id + f"-analysis-{direction}",
            )
            return direction, result

        with ThreadPoolExecutor(max_workers=len(collection_results)) as executor:
            futures = {
                executor.submit(analyze_single, d, data): d
                for d, data in collection_results.items()
            }
            for future in as_completed(futures):
                direction = futures[future]
                try:
                    results[direction] = future.result()[1]
                except Exception as e:
                    results[direction] = f"Error: {str(e)}"

        return results

    def _write_and_review(self, analysis_results: dict[str, str]) -> str:
        """报告撰写 + 审核"""
        import json

        # 报告撰写
        prompt = f"""作为报告撰写员，将以下分析结果整合为完整研究报告：

课题：{self.topic}

分析结果：
{json.dumps(analysis_results, ensure_ascii=False, indent=2)}

请按以下结构撰写完整报告：
1. 执行摘要
2. 研究背景与目的
3. 核心发现（按研究方向组织）
4. 深度分析
5. 未来展望
6. 结论与建议
7. 参考资料

报告要求：
- 用中文撰写
- 字数：8000-15000字
- 每个结论要有证据支撑
- 适当使用表格和列表

请直接输出完整报告内容。"""

        draft = self.client.chat(
            message=prompt,
            thread_id=self.thread_id + "-draft",
        )

        # 审核
        review_prompt = f"""作为审核员，审核以下研究报告：

报告：{draft}

请从以下维度审核：
1. 准确性：数据是否准确？来源是否可靠？
2. 逻辑性：章节逻辑是否清晰？推理是否合理？
3. 完整性：是否覆盖所有重要方面？
4. 可读性：语言是否清晰流畅？
5. 时效性：数据是否最新？

如果需要修改，请指出具体问题和修改建议。
如果报告质量合格，请明确说明"审核通过"。

请用中文输出审核报告。"""

        review = self.client.chat(
            message=review_prompt,
            thread_id=self.thread_id + "-review",
        )

        # 如果审核通过，返回最终报告；否则标记需修改
        if "审核通过" in review or "通过审核" in review:
            return draft
        else:
            # 反馈给撰写员修改
            revision_prompt = f"""请根据审核意见修改以下报告：

原报告：{draft}

审核意见：{review}

请基于审核意见修改报告，然后输出修改后的完整报告。

请用中文输出。"""

            final = self.client.chat(
                message=revision_prompt,
                thread_id=self.thread_id + "-revision",
            )
            return final

    def get_final_report(self) -> str | None:
        """获取最终报告"""
        return self.project.final_report

    def get_project_status(self) -> ResearchStatus:
        """获取项目状态"""
        return self.project.status

    def get_intermediate_outputs(self) -> dict[str, str]:
        """获取中间产出"""
        return {k: v.output for k, v in self.project.tasks.items() if v.output}
