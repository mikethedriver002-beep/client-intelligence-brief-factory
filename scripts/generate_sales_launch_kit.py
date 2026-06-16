#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

KIT_FILES = [
    "README.md",
    "01_cold_outreach_email.md",
    "02_linkedin_dm.md",
    "03_agency_pitch_one_pager.md",
    "04_pricing_packages.md",
    "05_onboarding_questionnaire.md",
    "06_sample_brief_offer.md",
    "07_prospect_target_list_structure.md",
    "08_objection_handling.md",
    "09_sales_process_sop.md",
    "prospect_target_list_template.csv",
    "first_25_prospects_canada_seed.csv",
    "outreach_batches/top5_canada_agency_outreach_batch_2026_06_16.md",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_index(output_dir: Path, copied_files: list[str]) -> None:
    lines = [
        "# Brief Factory v0.4 Sales Launch Kit",
        "",
        f"Generated: {now_utc()}",
        "",
        "## Start here",
        "",
        "1. Read `03_agency_pitch_one_pager.md` to understand the offer.",
        "2. Open `first_25_prospects_canada_seed.csv` for the researched first prospect list.",
        "3. Open `outreach_batches/top5_canada_agency_outreach_batch_2026_06_16.md` for send-ready top-5 outreach.",
        "4. Use `01_cold_outreach_email.md` and `02_linkedin_dm.md` for future outreach batches.",
        "5. Use `05_onboarding_questionnaire.md` after a prospect shows interest.",
        "6. Use `prospect_target_list_template.csv` to build the next prospect batch.",
        "7. Use `09_sales_process_sop.md` to run the first paid pilot process.",
        "",
        "## Files included",
        "",
    ]
    for file_name in copied_files:
        lines.append(f"- `{file_name}`")
    lines += [
        "",
        "## First sales goal",
        "",
        "Close one paid pilot: one agency, one client niche, one weekly brief, one month.",
        "",
    ]
    (output_dir / "SALES_LAUNCH_KIT_INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def zip_folder(output_dir: Path, zip_name: str) -> Path:
    zip_path = output_dir / zip_name
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in output_dir.rglob("*"):
            if path.is_file() and path.name != zip_path.name:
                archive.write(path, path.relative_to(output_dir))
    return zip_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Brief Factory v0.4 Sales Launch Kit")
    parser.add_argument("--kit-source", default="sales_launch_kit")
    parser.add_argument("--output-root", default="outputs/sales_launch_kit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.kit_source)
    output_dir = ensure_dir(Path(args.output_root) / "brief_factory_v0_4_sales_launch_kit")

    if not source_dir.exists():
        raise FileNotFoundError(f"Missing sales kit source directory: {source_dir}")

    copied: list[str] = []
    for file_name in KIT_FILES:
        src = source_dir / file_name
        if not src.exists():
            raise FileNotFoundError(f"Missing sales kit file: {src}")
        dest = output_dir / file_name
        ensure_dir(dest.parent)
        shutil.copyfile(src, dest)
        copied.append(file_name)

    write_index(output_dir, copied)
    copied.append("SALES_LAUNCH_KIT_INDEX.md")

    manifest = {
        "schema": "brief_factory.sales_launch_kit_manifest.v1",
        "version": "v0.4-prospect-seed-top5-outreach",
        "generated_at_utc": now_utc(),
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "files": copied,
        "first_sales_goal": "Close one paid pilot: one agency, one client niche, one weekly brief, one month.",
        "prospect_seed_file": "first_25_prospects_canada_seed.csv",
        "top5_outreach_batch": "outreach_batches/top5_canada_agency_outreach_batch_2026_06_16.md",
    }
    (output_dir / "sales_launch_kit_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    zip_path = zip_folder(output_dir, "brief_factory_v0_4_sales_launch_kit.zip")
    manifest["zip_path"] = str(zip_path)
    (output_dir / "sales_launch_kit_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "PASS",
        "output_dir": str(output_dir),
        "zip_path": str(zip_path),
        "files": len(copied),
        "prospect_seed_file": "first_25_prospects_canada_seed.csv",
        "top5_outreach_batch": "outreach_batches/top5_canada_agency_outreach_batch_2026_06_16.md",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
