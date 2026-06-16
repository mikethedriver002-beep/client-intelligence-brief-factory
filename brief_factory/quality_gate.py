from __future__ import annotations

from typing import Any, Dict, List


def run_quality_gate(items: List[Dict[str, Any]], client_config: Dict[str, Any], source_audit: Dict[str, Any] | None = None) -> Dict[str, Any]:
    minimum_items = int(client_config.get("quality", {}).get("minimum_items", 3))
    top_count = int(client_config.get("quality", {}).get("top_count", 5))
    top_items = items[:top_count]
    issues: List[Dict[str, str]] = []

    if len(items) < minimum_items:
        issues.append({"severity": "fail", "item_id": "brief", "issue": f"only {len(items)} items; minimum is {minimum_items}"})

    if source_audit and source_audit.get("counts", {}).get("fail", 0):
        issues.append({"severity": "fail", "item_id": "source_registry", "issue": f"{source_audit['counts']['fail']} source registry failures"})

    seen_titles = set()
    for item in items:
        title_key = item.get("title", "").strip().lower()
        if title_key in seen_titles:
            issues.append({"severity": "review", "item_id": item.get("item_id", ""), "issue": "duplicate title"})
        seen_titles.add(title_key)

    for item in top_items:
        item_id = item.get("item_id", "")
        if not item.get("source_urls"):
            issues.append({"severity": "fail", "item_id": item_id, "issue": "top item missing source URL"})
        if not item.get("source_timestamp"):
            issues.append({"severity": "review", "item_id": item_id, "issue": "top item missing source timestamp"})
        if not item.get("summary"):
            issues.append({"severity": "fail", "item_id": item_id, "issue": "top item missing summary"})
        if not item.get("why_it_matters"):
            issues.append({"severity": "review", "item_id": item_id, "issue": "missing why_it_matters"})
        if item.get("confidence") == "low" and not item.get("needs_review"):
            issues.append({"severity": "fail", "item_id": item_id, "issue": "low confidence item not marked needs_review"})

    fail_count = sum(1 for issue in issues if issue["severity"] == "fail")
    review_count = sum(1 for issue in issues if issue["severity"] == "review")
    return {
        "schema": "brief_factory.qa_report.v1",
        "passed": fail_count == 0,
        "fail_count": fail_count,
        "review_count": review_count,
        "issues": issues,
        "minimum_items": minimum_items,
        "items_checked": len(items),
    }
