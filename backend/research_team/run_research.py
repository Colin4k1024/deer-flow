#!/usr/bin/env python3
"""
深度研究团队启动器

用法:
    cd ~/Desktop/poc/deer-flow
    python -m research_team.run_research --topic "协作机器人最新进展" --directions "技术趋势" "市场分析" "应用案例"

    # 或者交互模式
    python -m research_team.run_research --interactive
"""

import argparse
import os
import sys

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="深度研究团队 - 前沿制造方向")
    parser.add_argument("--topic", type=str, help="研究课题")
    parser.add_argument("--directions", nargs="+", help="研究方向列表")
    parser.add_argument("--model", type=str, default="minimax-m2.7-highspeed", help="使用的模型")
    parser.add_argument("--output", type=str, default="./research_outputs", help="输出目录")
    parser.add_argument("--interactive", action="store_true", help="交互模式")

    args = parser.parse_args()

    if args.interactive:
        print("=" * 60)
        print("深度研究团队 - 交互模式")
        print("=" * 60)

        topic = input("\n请输入研究课题：")
        directions_input = input("研究方向（用逗号分隔，留空则综合研究）：")
        directions = [d.strip() for d in directions_input.split(",") if d.strip()] if directions_input.strip() else []

        print(f"\n研究课题：{topic}")
        print(f"研究方向：{directions if directions else '综合研究'}")
        print("\n开始研究...\n")
    else:
        if not args.topic:
            print("错误：请提供 --topic 参数，或使用 --interactive 交互模式")
            sys.exit(1)
        topic = args.topic
        directions = args.directions or []

    # 运行研究
    from research_team import ResearchTeam

    print("正在初始化研究团队...")
    print(f"模型：{args.model}")
    print(f"项目ID：{topic[:20]}...")

    team = ResearchTeam(
        topic=topic,
        directions=directions,
        model_name=args.model,
        output_dir=args.output,
    )

    print("\n开始执行研究计划...")
    print("-" * 40)

    try:
        project = team.run()

        if project.status.value == "completed":
            print("\n" + "=" * 60)
            print("研究完成！")
            print("=" * 60)

            output_path = os.path.join(args.output, f"final_report_{project.project_id}.md")
            os.makedirs(args.output, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(project.final_report or "")

            print(f"\n最终报告已保存至：{output_path}")
            print("\n报告预览（前2000字）：")
            print("-" * 40)
            print((project.final_report or "")[:2000])
        else:
            print(f"\n研究失败：{project.status.value}")

    except Exception as e:
        print(f"\n研究过程出错：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
