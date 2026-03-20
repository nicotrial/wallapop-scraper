#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_console import find_wallapop_categories

CATEGORY_BANNER = r"""
__        __    _ _                         _
\ \      / /_ _| | | __ _ _ __   ___  _ __| |
 \ \ /\ / / _` | | |/ _` | '_ \ / _ \| '__| |
  \ V  V / (_| | | | (_| | |_) | (_) | |  | |
   \_/\_/ \__,_|_|_|\__,_| .__/ \___/|_|  |_|
                         |_|

        Category Lookup CLI
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lookup Wallapop category IDs.")
    parser.add_argument("query", help="Category or product type to search for.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum number of matches.")
    parser.add_argument("--refresh", action="store_true", help="Refresh the cached categories from Wallapop.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.json:
        print(CATEGORY_BANNER)
    result = find_wallapop_categories(
        {
            "query": args.query,
            "limit": args.limit,
            "refresh": args.refresh,
        }
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if not result.get("ok"):
        raise SystemExit(result.get("error", "Category lookup failed."))

    categories = result.get("categories", [])
    if not categories:
        print("No categories found.")
        return

    for category in categories:
        print(f'{category["id"]}: {category["path"]}')


if __name__ == "__main__":
    main()
