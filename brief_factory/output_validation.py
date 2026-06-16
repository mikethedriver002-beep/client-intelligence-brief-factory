from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_OUTPUT_FILES = [
    "weekly_brief.md",
    "weekly_brief.html",
    "outreach_ready_sample.md",
    "outreach_ready_sample.html",
    "agency_sales_sample.md",
    "agency_sales_sample.html",
    "source_appendix.csv",
    "qa_report.md",
    "qa_report.json",
    "normalized_items.json",
    "delivery_manifest.json",
    "handoff_email.md",
]

REQUIRED_SOURCE_APPENDIX_COLUMNS = [
    "rank",
    "item_id",
    "title",
    "source_id",
    "source_type",
    "evidence_type",
    "source_url",
    "evidence_notes",
    "client_safe_caveat",
]


def _read_source_appendix(path: Path) -> tuple[List[str], List[Dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def validate_delivery_outputs(output_dir: Path, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate generated packet files after rendering.

    This is a code-output sanity check, separate from editorial QA. It catches
    broken wiring such as missing new v0.3.1 files or empty evidence columns.
    """

    issues: List[Dict[str, str]] = []
    for filename in REQUIRED_OUTPUT_FILES:
        path = output_dir / filename
        if not path.exists():
            issues.append({"severity": "fail", "file": filename, "issue": "required output file missing"})
        elif path.is_file() and path.stat().st_size == 0:
            issues.append({"severity": "fail", "file": filename, "issue": "required output file is empty"})

    appendix_path = output_dir / "source_appendix.csv"
    headers, rows = _read_source_appendix(appendix_path)
    if appendix_path.exists():
        missing_headers = [header for header in REQUIRED_SOURCE_APPENDIX_COLUMNS if header not in headers]
        for header in missing_headers:
            issues.append({"severity": "fail", "file": "source_appendix.csv", "issue": f"missing required column: {header}"})
        if len(rows) < len(items):
            issues.append({"severity": "review", "file": "source_appendix.csv", "issue": f"appendix rows {len(rows)} below item count {len(items)}"})
        for index, row in enumerate(rows, start=1):
            if not row.get("source_id"):
                issues.append({"severity": "review", "file": "source_appendix.csv", "issue": f"row {index} missing source_id"})
            if not row.get("source_type"):
                issues.append({"severity": "review", "file": "source_appendix.csv", "issue": f"row {index} missing source_type"})
            if not row.get("evidence_type"):
                issues.append({"severity": "review", "file": "source_appendix.csv", "issue": f"row {index} missing evidence_type"})
            if not row.get("client_safe_caveat"):
                issues.append({"severity": "review", "file": "source_appendix.csv", "issue": f"row {index} missing client_safe_caveat"})

    fail_count = sum(1 for issue in issues if issue["severity"] == "fail")
    review_count = sum(1 for issue in issues if issue["severity"] == "review")
    status = "FAIL" if fail_count else "REVIEW" if review_count else "PASS"
    return {
        "schema": "brief_factory.output_validation.v1",
        "status": status,
        "fail_count": fail_count,
        "review_count": review_count,
        "required_files": REQUIRED_OUTPUT_FILES,
        "required_source_appendix_columns": REQUIRED_SOURCE_APPENDIX_COLUMNS,
        "issues": issues,
    }
