from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from .utils import clean, now_utc, read_json, url_ok, write_csv, write_json

AUDIT_FIELDS = [
    "source_id",
    "name",
    "source_type",
    "tier",
    "trust_band",
    "enabled",
    "allowed_use",
    "publish_policy",
    "status",
    "issues",
    "urls_count",
    "domains_count",
]

GREEN_TIERS = {"official", "primary", "operator", "wire", "public_database", "client_approved"}
YELLOW_TIERS = {"discovery", "media", "social_manual", "community", "review_only"}
RED_TIERS = {"red", "prohibited", "login_gated", "paywalled", "vendor_restricted"}


def canonical_band(source: Dict[str, Any]) -> str:
    raw = clean(source.get("trust_band")).lower()
    tier = clean(source.get("tier")).lower()
    if "red" in raw or tier in RED_TIERS:
        return "red"
    if "green" in raw or tier in GREEN_TIERS:
        return "green"
    if "yellow" in raw or tier in YELLOW_TIERS:
        return "yellow"
    return "yellow"


def audit_source(source: Dict[str, Any], seen: set[str]) -> Dict[str, Any]:
    issues: List[str] = []
    source_id = clean(source.get("source_id"))
    source_type = clean(source.get("source_type"))
    tier = clean(source.get("tier"))
    band = canonical_band(source)
    enabled = bool(source.get("enabled"))
    urls = source.get("urls") or []
    domains = source.get("domains") or []
    allowed_use = source.get("allowed_use") or []

    if not source_id:
        issues.append("missing source_id")
    elif source_id in seen:
        issues.append("duplicate source_id")
    seen.add(source_id)

    if not clean(source.get("name")):
        issues.append("missing name")
    if not source_type:
        issues.append("missing source_type")
    if not tier:
        issues.append("missing tier")
    if band == "red" and enabled:
        issues.append("red/prohibited source cannot be enabled")
    if enabled and source_type not in {"manual", "rss", "html", "official_site", "public_database"}:
        issues.append(f"unsupported enabled source_type={source_type}")
    if enabled and source_type in {"rss", "html", "official_site", "public_database"} and not urls:
        issues.append("enabled web source should include at least one URL")
    for url in urls:
        if not url_ok(url):
            issues.append(f"bad url: {url}")
            break
    if not clean(source.get("publish_policy")):
        issues.append("missing publish_policy")
    if not allowed_use:
        issues.append("missing allowed_use")
    if source.get("requires_login"):
        issues.append("requires_login=true; keep disabled unless client explicitly supplies/permits access")
    if source.get("resale_restricted"):
        issues.append("resale_restricted=true; do not use in client-facing deliverables")

    severe = [issue for issue in issues if "cannot" in issue or "bad url" in issue or "resale_restricted" in issue or "requires_login" in issue]
    status = "PASS" if not issues else "FAIL" if severe else "REVIEW"

    return {
        "source_id": source_id,
        "name": clean(source.get("name")),
        "source_type": source_type,
        "tier": tier,
        "trust_band": band,
        "enabled": "Yes" if enabled else "No",
        "allowed_use": "; ".join(allowed_use),
        "publish_policy": clean(source.get("publish_policy")),
        "status": status,
        "issues": "; ".join(issues),
        "urls_count": len(urls),
        "domains_count": len(domains),
    }


def audit_registry(registry_path: Path, output_dir: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    raw = read_json(registry_path)
    sources = raw.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("source registry must contain a 'sources' list")

    seen: set[str] = set()
    rows = [audit_source(source, seen) for source in sources if isinstance(source, dict)]
    counts = {
        "sources": len(rows),
        "green": sum(1 for row in rows if row["trust_band"] == "green"),
        "yellow": sum(1 for row in rows if row["trust_band"] == "yellow"),
        "red": sum(1 for row in rows if row["trust_band"] == "red"),
        "pass": sum(1 for row in rows if row["status"] == "PASS"),
        "review": sum(1 for row in rows if row["status"] == "REVIEW"),
        "fail": sum(1 for row in rows if row["status"] == "FAIL"),
    }
    report = {
        "schema": "brief_factory.source_audit.v1",
        "generated_at_utc": now_utc(),
        "registry_version": raw.get("registry_version", ""),
        "counts": counts,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "source_audit.json", report)
    write_csv(output_dir / "source_audit.csv", rows, AUDIT_FIELDS)

    lines = [
        "# Source Registry Audit",
        "",
        f"Generated: {report['generated_at_utc']}",
        f"Registry version: {report['registry_version']}",
        "",
        f"- total sources: {counts['sources']}",
        f"- green: {counts['green']}",
        f"- yellow: {counts['yellow']}",
        f"- red: {counts['red']}",
        f"- pass: {counts['pass']}",
        f"- review: {counts['review']}",
        f"- fail: {counts['fail']}",
        "",
        "## Sources needing attention",
        "",
    ]
    attention = [row for row in rows if row["status"] != "PASS"]
    if attention:
        for row in attention:
            lines.append(f"- **{row['status']}** | {row['source_id']} | {row['issues']}")
    else:
        lines.append("No source registry issues detected.")
    (output_dir / "source_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report, rows
