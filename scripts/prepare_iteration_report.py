from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse


TEMPLATE = """# Product Iteration Report - {date}

## Competitor signals

- 

## What we can adopt

- 

## What changed today

- 

## Regression

- Pending

## Next candidate

- 
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
