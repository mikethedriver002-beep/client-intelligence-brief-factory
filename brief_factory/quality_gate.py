from __future__ import annotations

from typing import Any, Dict, List


REVIEW_COMPLETE_STATUSES = {"approved", "complete", "completed", "operator_verified", "client_ready", "ready"}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _clean(value).lower() in {"1", "true", "yes", "y", "approved", "complete", "completed"}


def _human_review_state(client_config: Dict[str, Any]) -> tuple[bool, bool]:
    delivery = client_config.get("delivery", {}) if isinstance(client_config.get("delivery", {}), dict) else {}
    approval = client_config.get("approval", {}) if isinstance(client_config.get("approval", {}), dict) else {}

    required = delivery.get("human_review_required", approval.get("human_review_required", True))
    human_review_required = _as_bool(required) if required is not None else True

    complete_value = (
        delivery.get("human_review_complete")
        if "human_review_complete" in delivery
        else approval.get("human_review_complete", approval.get("review_complete"))
    )
    status_value = _clean(delivery.get("review_status") or approval.get("review_status")).lower()
    human_review_complete = _as_bool(complete_value) or status_value in REVIEW_COMPLETE_STATUSES

    return human_review_required, human_review_complete


def run_quality_gate(items: List[Dict[str, Any]], client_config: Dict[str, Any], source_audit: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Return an honest delivery status for a generated brief packet.

    Status meanings:
    - PASS: technically valid and client-ready.
    - PASS_WITH_REVIEW: generated successfully, but human review or item review is still required.
    - FAIL: missing required material or source rules failed.
    """

    minimum_items = int(client_config.get("quality", {}).get("minimum_items", 3))
    top_count = int(client_config.get("quality", {}).get("top_count", 5))
    top_items = items[:top_count]
    issues: List[Dict[str, str]] = []

    if len(items) < minimum_items:
        issues.append({"severity": "fail", "item_id": "brief", "issue": f"only {len(items)} items; minimum is {minimum_items}"})

    if source_audit:
        source_counts = source_audit.get("counts", {})
        if source_counts.get("fail", 0):
            issues.append({"severity": "fail", "item_id": "source_registry", "issue": f"{source_counts['fail']} source registry failures"})
        if source_counts.get("review", 0):
            issues.append({"severity": "review", "item_id": "source_registry", "issue": f"{source_counts['review']} source registry rows need review"})

    seen_titles = set()
    for item in items:
        item_id = item.get("item_id", "")
        title_key = item.get("title", "").strip().lower()
        if title_key in seen_titles:
            issues.append({"severity": "review", "item_id": item_id, "issue": "duplicate title"})
        seen_titles.add(title_key)

        if item.get("needs_review"):
            reasons = item.get("review_reasons") or ["item marked needs_review"]
            issues.append({
                "severity": "review",
                "item_id": item_id,
                "issue": "item needs human review: " + "; ".join(str(reason) for reason in reasons),
            })

    for item in top_items:
        item_id = item.get("item_id", "")
        if not item.get("source_urls"):
            issues.append({"severity": "fail", "item_id": item_id, "issue": "top item missing source URL"})
        if not item.get("source_timestamp"):
            issues.append({"severity": "review", "item_id": item_id, "issue": "top item missing source timestamp"})
        if not item.get("source_id"):
            issues.append({"severity": "review", "item_id": item_id, "issue": "top item missing source_id"})
        if not item.get("source_type"):
            issues.append({"severity": "review", "item_id": item_id, "issue": "top item missing source_type"})
        if not item.get("evidence_type"):
            issues.append({"severity": "review", "item_id": item_id, "issue": "top item missing evidence_type"})
        if not item.get("summary"):
            issues.append({"severity": "fail", "item_id": item_id, "issue": "top item missing summary"})
        if not item.get("why_it_matters"):
            issues.append({"severity": "review", "item_id": item_id, "issue": "missing why_it_matters"})
        if item.get("confidence") == "low" and not item.get("needs_review"):
            issues.append({"severity": "fail", "item_id": item_id, "issue": "low confidence item not marked needs_review"})

    human_review_required, human_review_complete = _human_review_state(client_config)
    if human_review_required and not human_review_complete:
        issues.append({"severity": "review", "item_id": "human_review", "issue": "human review required before client delivery"})

    fail_count = sum(1 for issue in issues if issue["severity"] == "fail")
    review_count = sum(1 for issue in issues if issue["severity"] == "review")
    needs_review_count = sum(1 for item in items if item.get("needs_review"))

    if fail_count:
        status = "FAIL"
    elif review_count:
        status = "PASS_WITH_REVIEW"
    else:
        status = "PASS"

    client_ready = status == "PASS"
    warning = ""
    if status == "PASS_WITH_REVIEW":
        warning = "Not client-ready until human review is complete."
    elif status == "FAIL":
        warning = "Not client-ready. Fix failed QA items before delivery."

    return {
        "schema": "brief_factory.qa_report.v1",
        "status": status,
        "passed": fail_count == 0,
        "client_ready": client_ready,
        "warning": warning,
        "fail_count": fail_count,
        "review_count": review_count,
        "needs_review_count": needs_review_count,
        "human_review_required": human_review_required,
        "human_review_complete": human_review_complete,
        "issues": issues,
        "minimum_items": minimum_items,
        "items_checked": len(items),
    }
