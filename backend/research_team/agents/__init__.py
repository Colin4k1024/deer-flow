"""
Research Team Agents for DeerFlow
自定义角色 Agent：首席研究员、信息搜集员、分析员、报告撰写员、审核员
"""

from .analyst import ANALYST_PROMPT
from .information_collector import INFORMATION_COLLECTOR_PROMPT
from .lead_researcher import LEAD_RESEARCHER_PROMPT
from .report_writer import REPORT_WRITER_PROMPT
from .reviewer import REVIEWER_PROMPT

ROLE_AGENTS = {
    "lead_researcher": {
        "name": "首席研究员",
        "description": "制定研究计划、拆解任务、把控质量、输出最终报告",
        "prompt": LEAD_RESEARCHER_PROMPT,
    },
    "information_collector": {
        "name": "信息搜集员",
        "description": "广泛搜集资料、爬取内容、整理汇编",
        "prompt": INFORMATION_COLLECTOR_PROMPT,
    },
    "analyst": {
        "name": "分析师",
        "description": "提炼洞察、发现关联、分析趋势",
        "prompt": ANALYST_PROMPT,
    },
    "report_writer": {
        "name": "报告撰写员",
        "description": "撰写结构化研究报告",
        "prompt": REPORT_WRITER_PROMPT,
    },
    "reviewer": {
        "name": "审核员",
        "description": "质量把关、逻辑校验、提出修改意见",
        "prompt": REVIEWER_PROMPT,
    },
}
