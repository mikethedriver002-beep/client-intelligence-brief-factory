#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from a fresh checkout without installing the package.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brief_factory.manual_ingest import ingest_manual_csv
from brief_factory.normalizer import normalize_items
from brief_factory.packager import build_zip
from brief_factory.quality_gate import run_quality_gate
from brief_factory.ranker import rank_items
from brief_factory.render import write_delivery_files
from brief_factory.rss_ingest import ingest_enabled_rss_sources
from brief_factory.source_audit import audit_registry
from brief_factory.utils import ensure_dir, now_utc, read_json, slugify, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Brief Factory")
    parser.add_argument("--client-config", default="config/clients/demo_local_seo_client.json")
    parser.add_argument("--source-registry", default="config/source_registries/demo_local_seo_sources.json")
    parser.add_argument("--manual-csv", default="data/inbox/demo_manual_items.csv")
    parser.add_argument("--output-root", default="outputs/brief_factory")
    parser.add_argument("--run-mode", choices=["source_audit_only", "draft_brief", "full_delivery_packet"], default="full_delivery_packet")
    parser.add_argument("--enable-network", action="store_true", help="Allow RSS network fetching. Manual intake works without this.")
    parser.add_argument("--strict-qa", action="store_true", help="Exit non-zero only if QA status is FAIL.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client_config = read_json(Path(args.client_config))
    registry = read_json(Path(args.source_registry))

    run_id = f"{now_utc().replace(':', '').replace('+0000', 'Z').replace('+00:00', 'Z')}-{slugify(client_config.get('client_id', 'client'))}"
    output_dir = ensure_dir(Path(args.output_root) / slugify(client_config.get("agency_id", "agency")) / slugify(client_config.get("client_id", "client")) / run_id)

    source_audit, audit_rows = audit_registry(Path(args.source_registry), output_dir)

    if args.run_mode == "source_audit_only":
        manifest = {
            "schema": "brief_factory.delivery_manifest.v1",
            "run_id": run_id,
            "generated_at_utc": now_utc(),
            "run_mode": args.run_mode,
            "client_config": args.client_config,
            "source_registry": args.source_registry,
            "client_ready": False,
            "client_ready_warning": "Source audit only. No client delivery packet was generated.",
            "source_audit": source_audit,
            "outputs": ["source_audit.md", "source_audit.csv", "source_audit.json"],
        }
        write_json(output_dir / "delivery_manifest.json", manifest)
        print(f"Source audit complete: {output_dir}")
        return 0

    raw_items = []
    raw_items.extend(ingest_manual_csv(Path(args.manual_csv)))
    raw_items.extend(ingest_enabled_rss_sources(registry, enable_network=args.enable_network))

    normalized = normalize_items(raw_items, client_config)
    ranked = rank_items(normalized, client_config)
    qa_report = run_quality_gate(ranked, client_config, source_audit=source_audit)

    manifest = {
        "schema": "brief_factory.delivery_manifest.v1",
        "run_id": run_id,
        "generated_at_utc": now_utc(),
        "run_mode": args.run_mode,
        "client_config": args.client_config,
        "source_registry": args.source_registry,
        "manual_csv": args.manual_csv,
        "network_enabled": bool(args.enable_network),
        "item_counts": {
            "raw": len(raw_items),
            "normalized": len(normalized),
            "ranked": len(ranked),
        },
        "qa_status": qa_report.get("status"),
        "qa_passed": qa_report.get("passed"),
        "client_ready": qa_report.get("client_ready"),
        "client_ready_warning": qa_report.get("warning"),
        "fail_count": qa_report.get("fail_count"),
        "review_count": qa_report.get("review_count"),
        "needs_review_count": qa_report.get("needs_review_count"),
        "human_review_required": qa_report.get("human_review_required"),
        "human_review_complete": qa_report.get("human_review_complete"),
        "source_audit": source_audit,
    }

    write_delivery_files(output_dir, client_config, ranked, qa_report, manifest)

    if args.run_mode == "full_delivery_packet":
        zip_path = build_zip(output_dir)
        manifest["delivery_zip"] = str(zip_path)
        write_json(output_dir / "delivery_manifest.json", manifest)

    print(f"Brief Factory run complete: {output_dir}")
    print(f"QA status: {qa_report.get('status')}")
    print(f"Client ready: {qa_report.get('client_ready')}")
    if qa_report.get("warning"):
        print(f"Warning: {qa_report.get('warning')}")
    if args.strict_qa and qa_report.get("status") == "FAIL":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
