#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brief_factory.sales_ops import run_sales_ops_control_center


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Brief Factory v0.5 Sales Ops Control Center")
    parser.add_argument(
        "--tracker-csv",
        default="sales_launch_kit/contact_enrichment/send_day_tracker_batch_001_2026_06_16.csv",
        help="CSV tracker containing prospect send, follow-up, and reply statuses.",
    )
    parser.add_argument(
        "--output-root",
        default="outputs/sales_ops",
        help="Output root for generated sales ops packets.",
    )
    parser.add_argument(
        "--as-of-date",
        default=None,
        help="Optional YYYY-MM-DD date used to decide whether follow-ups are due.",
    )
    parser.add_argument(
        "--sender",
        default="michael@brieffactory.com",
        help="Sender email used in generated follow-up and reply scripts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = run_sales_ops_control_center(
        tracker_csv=args.tracker_csv,
        output_root=args.output_root,
        as_of_date=args.as_of_date,
        sender=args.sender,
    )
    print(json.dumps({
        "status": "PASS",
        "version": manifest.get("version"),
        "as_of_date": manifest.get("as_of_date"),
        "output_dir": manifest.get("output_dir"),
        "zip_path": manifest.get("zip_path"),
        "prospects_tracked": manifest.get("prospects_tracked"),
        "actions_due": manifest.get("actions_due"),
        "followups_due": manifest.get("followups_due"),
        "stage_counts": manifest.get("stage_counts"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
