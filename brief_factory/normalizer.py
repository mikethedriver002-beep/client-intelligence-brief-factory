from __future__ import annotations

from typing import Any, Dict, List

from .utils import clean, now_utc, split_list, stable_id, url_ok


APPROVED_STATUSES = {"approved", "operator_verified", "verified", "complete", "completed", "client_ready", "ready"}


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return clean(value).lower() in {"1", "true", "yes", "y"}


def normalize_item(raw: Dict[str, Any], client_config: Dict[str, Any]) -> Dict[str, Any]:
    title = clean(raw.get("title") or raw.get("headline"))
    summary = clean(raw.get("summary"))
    source_urls = [url for url in split_list(raw.get("source_urls")) if url_ok(url)]
    source_timestamp = clean(raw.get("source_timestamp"))
    confidence = clean(raw.get("confidence")).lower() or "medium"
    urgency = clean(raw.get("urgency")).lower() or "medium"
    category = clean(raw.get("category")).lower() or "market_signal"
    status = clean(raw.get("status")).lower() or "ready_for_review"
    review_status = clean(raw.get("review_status")).lower()
    explicit_needs_review = _as_bool(raw.get("needs_review"))
    needs_review_reasons: List[str] = []

    if not title:
        needs_review_reasons.append("missing title")
    if not summary:
        needs_review_reasons.append("missing summary")
    if not source_urls:
        needs_review_reasons.append("missing valid source URL")
    if not source_timestamp:
        needs_review_reasons.append("missing source timestamp")
    if confidence == "low":
        needs_review_reasons.append("low confidence")
    if explicit_needs_review:
        needs_review_reasons.append("manual needs_review flag")
    if "review" in status and status not in APPROVED_STATUSES:
        needs_review_reasons.append("status requires review")
    if review_status and review_status not in APPROVED_STATUSES:
        needs_review_reasons.append(f"review_status={review_status}")

    item_id = clean(raw.get("item_id")) or stable_id("brief", title, summary, ";".join(source_urls))
    return {
        "schema": "brief_factory.brief_item.v1",
        "item_id": item_id,
        "client_id": client_config.get("client_id"),
        "agency_id": client_config.get("agency_id"),
        "generated_at_utc": now_utc(),
        "title": title or "Untitled brief item",
        "summary": summary,
        "why_it_matters": clean(raw.get("why_it_matters")) or "Add analyst interpretation before delivery.",
        "recommended_action": clean(raw.get("recommended_action")) or "Review before client delivery.",
        "category": category,
        "urgency": urgency,
        "confidence": confidence,
        "source_name": clean(raw.get("source_name")),
        "source_id": clean(raw.get("source_id")),
        "source_urls": source_urls,
        "source_timestamp": source_timestamp,
        "tags": split_list(raw.get("tags")),
        "status": status,
        "review_status": review_status,
        "notes": clean(raw.get("notes")),
        "needs_review": bool(needs_review_reasons),
        "review_reasons": needs_review_reasons,
        "raw_source": clean(raw.get("raw_source")),
    }


def normalize_items(raw_items: List[Dict[str, Any]], client_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    seen = set()
    normalized: List[Dict[str, Any]] = []
    for raw in raw_items:
        item = normalize_item(raw, client_config)
        key = (item["title"].lower(), tuple(item["source_urls"]))
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    return normalized
