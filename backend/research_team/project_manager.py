"""
研究团队 - 项目管理器

负责异步任务调度、进度更新、状态持久化
"""

import asyncio
import json
import sys
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path

# 确保 deerflow 包在路径中
_backend = Path(__file__).parent.parent / "backend"  # noqa: E402
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))  # noqa: E402

from .client_safe import get_client  # noqa: E402
from .database import create_output, create_project, get_project, update_project  # noqa: E402
from .models import (  # noqa: E402
    ResearchOutputEntity,
    ResearchPhase,
    ResearchProjectEntity,
    ResearchStatus,
)

# ============================================================================
# 进度回调类型
# ============================================================================

ProgressCallback = Callable[[ResearchPhase, int, str | None], Awaitable[None]]


# ============================================================================
# 研究任务执行器
# ============================================================================


class AsyncResearchTeam:
    """
    异步研究团队执行器

    支持：
    - 异步执行
    - 进度回调
    - 任务取消
    - 断点续传

    使用方式：
        executor = AsyncResearchTeam(
            project_id="proj_123",
            topic="协作机器人趋势",
            directions=["技术趋势", "市场分析"],
            user_id="user_456",
            progress_callback=my_callback,
        )
        await executor.run()
    """

    def __init__(
        self,
        project_id: str,
        topic: str,
        directions: list[str],
        user_id: str,
        model_name: str = "minimax-m2.7-highspeed",
        output_dir: str = "./research_outputs",
        progress_callback: ProgressCallback | None = None,
    ):
        self.project_id = project_id
        self.topic = topic
        self.directions = directions or []
        self.user_id = user_id
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.progress_callback = progress_callback

        self._canceled = False

    # --------------------------------------------------------------------------
    # 公共方法
    # --------------------------------------------------------------------------

    async def run(self) -> dict:
        """
        执行完整的研究流程

        Returns:
            包含最终报告和中间产出的字典
        """
        try:
            # 阶段1：制定计划
            await self._update_progress(ResearchPhase.PLANNING, 10)
            plan = await self._lead_researcher_plan()
            await self._save_output(ResearchPhase.PLANNING, None, plan.get("plan", ""))

            # 阶段2：并行信息搜集
            await self._update_progress(ResearchPhase.COLLECTING, 20)
            collection_results = await self._parallel_collection(self.directions)
            for direction, content in collection_results.items():
                await self._save_output(ResearchPhase.COLLECTING, direction, content)

            # 阶段3：并行分析
            await self._update_progress(ResearchPhase.ANALYZING, 50)
            analysis_results = await self._parallel_analysis(collection_results)
            for direction, content in analysis_results.items():
                await self._save_output(ResearchPhase.ANALYZING, direction, content)

            # 阶段4：报告撰写
            await self._update_progress(ResearchPhase.WRITING, 70)
            draft = await self._write_draft(analysis_results)
            await self._save_output(ResearchPhase.WRITING, None, draft)

            # 阶段5：审核
            await self._update_progress(ResearchPhase.REVIEWING, 85)
            final_report = await self._review_and_revise(draft)

            # 保存报告到文件
            report_path = await self._save_report(final_report)

            # 完成
            await self._update_progress(ResearchPhase.COMPLETED, 100)
            await update_project(
                self.project_id,
                status=ResearchStatus.COMPLETED,
                progress=100,
                final_report_path=str(report_path),
            )

            return {
                "status": "completed",
                "final_report": final_report,
                "report_path": str(report_path),
                "outputs": {
                    "plan": plan,
                    "collection": collection_results,
                    "analysis": analysis_results,
                },
            }

        except asyncio.CancelledError:
            await update_project(
                self.project_id,
                status=ResearchStatus.CANCELLED,
            )
            raise

        except Exception as e:
            await update_project(
                self.project_id,
                status=ResearchStatus.FAILED,
                error_message=str(e),
            )
            raise

    def cancel(self) -> None:
        """取消任务"""
        self._canceled = True

    # --------------------------------------------------------------------------
    # 私有方法
    # --------------------------------------------------------------------------

    async def _update_progress(
        self,
        phase: ResearchPhase,
        progress: int,
        message: str | None = None,
    ) -> None:
        """更新进度（数据库 + 回调）"""
        if self._canceled:
            raise asyncio.CancelledError("Task was canceled")

        await update_project(
            self.project_id,
            status=ResearchStatus.IN_PROGRESS,
            progress=progress,
            current_phase=phase,
        )

        if self.progress_callback:
            await self.progress_callback(phase, progress, message)

    async def _save_output(
        self,
        phase: ResearchPhase,
        direction: str | None,
        content: str,
    ) -> None:
        """保存阶段产出到数据库"""
        output_id = f"out_{uuid.uuid4().hex[:8]}"
        entity = ResearchOutputEntity(
            output_id=output_id,
            project_id=self.project_id,
            phase=phase,
            direction=direction,
            content=content,
        )
        await create_output(entity)

    async def _lead_researcher_plan(self) -> dict:
        """首席研究员制定计划"""
        client = get_client(
            model_name=self.model_name,
            thinking_enabled=True,
            subagent_enabled=True,
        )
        thread_id = f"research-{self.project_id}-plan"

        prompt = f"""作为首席研究员，为以下研究课题制定详细研究计划：

课题：{self.topic}
研究方向：{', '.join(self.directions) if self.directions else '综合研究'}

请输出：
1. 具体研究范围和边界
2. 关键研究问题（3-5个）
3. 研究任务分解（列出每个研究方向的具体任务）
4. 预期产出

请用中文输出。"""

        response = client.chat(message=prompt, thread_id=thread_id)
        return {"plan": response}

    async def _parallel_collection(self, directions: list[str]) -> dict[str, str]:
        """并行信息搜集"""
        if not directions:
            directions = ["综合研究"]

        async def collect_single(direction: str) -> tuple[str, str]:
            client = get_client(
                model_name=self.model_name,
                thinking_enabled=True,
                subagent_enabled=True,
            )
            thread_id = f"research-{self.project_id}-collect-{direction}"

            prompt = f"""作为信息搜集员，深入研究以下课题：

课题：{self.topic}
方向：{direction}

请严格按照 deep-research skill 执行：
1. 广泛搜索 - 从多个角度搜索相关信息
2. 深度爬取 - 获取重要网页的完整内容
3. 整理汇编 - 按主题分类整理所有资料

输出：结构化的资料汇编，包含标题、链接、摘要、来源。

请用中文输出。"""

            result = client.chat(message=prompt, thread_id=thread_id)
            return direction, result

        # 并发执行所有搜集任务
        tasks = [collect_single(d) for d in directions]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for i, result in enumerate(results_list):
            direction = directions[i]
            if isinstance(result, Exception):
                results[direction] = f"Error: {str(result)}"
            else:
                results[result[0]] = result[1]

        return results

    async def _parallel_analysis(self, collection_results: dict[str, str]) -> dict[str, str]:
        """并行分析"""
        async def analyze_single(direction: str, data: str) -> tuple[str, str]:
            client = get_client(
                model_name=self.model_name,
                thinking_enabled=True,
                subagent_enabled=True,
            )
            thread_id = f"research-{self.project_id}-analysis-{direction}"

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

            result = client.chat(message=prompt, thread_id=thread_id)
            return direction, result

        # 并发执行所有分析任务
        tasks = [
            analyze_single(direction, data)
            for direction, data in collection_results.items()
        ]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        directions = list(collection_results.keys())
        for i, result in enumerate(results_list):
            direction = directions[i]
            if isinstance(result, Exception):
                results[direction] = f"Error: {str(result)}"
            else:
                results[result[0]] = result[1]

        return results

    async def _write_draft(self, analysis_results: dict[str, str]) -> str:
        """撰写报告草稿"""
        client = get_client(
            model_name=self.model_name,
            thinking_enabled=True,
            subagent_enabled=True,
        )
        thread_id = f"research-{self.project_id}-draft"

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

        return client.chat(message=prompt, thread_id=thread_id)

    async def _review_and_revise(self, draft: str) -> str:
        """审核并修订报告"""
        client = get_client(
            model_name=self.model_name,
            thinking_enabled=True,
            subagent_enabled=True,
        )
        thread_id = f"research-{self.project_id}-review"

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

        review = client.chat(message=review_prompt, thread_id=thread_id)

        # 如果审核通过，返回最终报告；否则修订
        if "审核通过" in review or "通过审核" in review:
            return draft

        # 修订
        revision_prompt = f"""请根据审核意见修改以下报告：

原报告：{draft}

审核意见：{review}

请基于审核意见修改报告，然后输出修改后的完整报告。

请用中文输出。"""

        return client.chat(message=revision_prompt, thread_id=thread_id)

    async def _save_report(self, report: str) -> Path:
        """保存报告到文件"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.output_dir / f"{self.project_id}_final.md"

        report_path.write_text(report, encoding="utf-8")
        return report_path


# ============================================================================
# 项目管理器
# ============================================================================


class ProjectManager:
    """
    研究项目管理器

    负责：
    - 创建项目
    - 调度异步任务
    - 任务状态查询
    """

    def __init__(self, output_dir: str = "./research_outputs"):
        self.output_dir = Path(output_dir)

    async def create_project(
        self,
        topic: str,
        directions: list[str],
        user_id: str,
        model_name: str = "minimax-m2.7-highspeed",
    ) -> ResearchProjectEntity:
        """
        创建新研究项目

        Args:
            topic: 研究课题
            directions: 研究方向
            user_id: 用户ID
            model_name: 模型名称

        Returns:
            创建的项目实体
        """
        project_id = f"proj_{uuid.uuid4().hex[:8]}"

        entity = ResearchProjectEntity(
            project_id=project_id,
            user_id=user_id,
            topic=topic,
            directions=directions,
            status=ResearchStatus.PENDING,
            progress=0,
        )

        await create_project(entity)
        return entity

    async def start_research(
        self,
        project_id: str,
        topic: str,
        directions: list[str],
        user_id: str,
        model_name: str = "minimax-m2.7-highspeed",
        progress_callback: ProgressCallback | None = None,
    ) -> AsyncResearchTeam:
        """
        启动研究任务

        Returns:
            AsyncResearchTeam 实例（尚未执行，需调用 run()）
        """
        executor = AsyncResearchTeam(
            project_id=project_id,
            topic=topic,
            directions=directions,
            user_id=user_id,
            model_name=model_name,
            output_dir=str(self.output_dir),
            progress_callback=progress_callback,
        )
        return executor

    async def get_project(self, project_id: str) -> ResearchProjectEntity | None:
        """获取项目信息"""
        return await get_project(project_id)
