from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse


TEMPLATE = """# Research Atlas 产品迭代日报 - {date}

## Executive summary

- 今天先完成竞品扫描、产品判断和一项低风险动作；如果当天没有安全改动，也要明确记录原因。
- 这份日报会作为桌面阅读版的源文件，因此首屏结论要短、要能直接告诉人“今天值得关注什么”。

## Competitor signals

- Litmaps：把“持续跟踪”做成研究流，比一次性搜索更容易形成长期价值。
- ResearchRabbit：从种子论文往外扩展的发现路径很顺，说明探索体验要尽量少打断。
- Semantic Scholar：仪表盘和提醒机制很强，适合把高频关注主题沉淀成长期订阅。
- SciSpace：单篇论文阅读辅助做得深，证明“读懂一篇”本身就值得单独打磨。

## What we can adopt

- 为主题或关键词做持续跟踪，而不是只提供静态结果页。
- 让日报、归档和桌面阅读文件形成固定交付，减少每天重新找入口的成本。
- 阅读层继续保持结构化输出，优先帮助用户判断“这篇值不值得细读”。

## What changed today

- 待补充

## Regression

- `python3 -m unittest discover -s tests -p 'test_*.py'`：待运行
- `python3 -m compileall backend frontend tests scripts`：待运行

## Next candidate

- 把个人工作区和账号体系接起来，让收藏、待读、备注真正变成私有空间。

## Sources

- Litmaps: https://www.litmaps.com/about/for-researchers
- ResearchRabbit: https://www.researchrabbit.ai/articles/guide-to-using-researchrabbit
- Semantic Scholar: https://www.semanticscholar.org/product
- SciSpace: https://scispace.com/resources/ultimate-guide-literature-review/
"""


def build_report_path(project_root: Path, report_date: str) -> Path:
    return project_root / "reports" / "product-iterations" / f"{report_date}.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a dated product iteration report file.")
    parser.add_argument("--date", dest="report_date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    report_path = build_report_path(project_root, args.report_date)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if not report_path.exists():
        report_path.write_text(TEMPLATE.format(date=args.report_date), encoding="utf-8")
    print(report_path)


if __name__ == "__main__":
    main()
