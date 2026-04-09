from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.container import build_container


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh a conference dataset into the local cache.")
    parser.add_argument("--conference", required=True, choices=["acl", "neurips", "iclr", "icml"])
    parser.add_argument("--year", required=True, type=int)
    args = parser.parse_args()

    container = build_container()
    result = container.paper_service.refresh_dataset(args.conference, args.year)
    print(
        f"Refreshed {result['conference'].upper()} {result['year']}: "
        f"{result['item_count']} papers, status={result['status']}"
    )


if __name__ == "__main__":
    main()
