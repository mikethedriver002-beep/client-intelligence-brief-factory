from __future__ import annotations

from typing import Any, Dict, List

from .utils import clean, now_utc, split_list, stable_id, url_ok


APPROVED_STATUSES = {"approved", "operator_verified", "verified", "complete", "completed", "client_ready", "ready"}
VALID_URGENCIES = {"critical", "high", "medium", "low"}
VALID_CONFIDENCE = {"high", "medium", "low"}


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return clean(value).lower() in {"1", "true", "yes", "y"}


def infer_evidence_type(raw: Dict[str, Any], category: str) -> str:
    explicit = clean(raw.get("evidence_type"))
    if explicit:
        return explicit

    source_type = clean(raw.get("source_type")).lower()
    source_id = clean(raw.get("source_id")).lower()
    source_name = clean(raw.get("source_name")).lower()
    text = " ".join([source_type, source_id, source_name, category])

    if source_type == "rss":
        return "rss_discovery"
    if "event" in category or "opportunity" in category or "event" in text or "cne" in text or "chamber" in text:
        return "event_watch"
    if "market" in category or "trend" in text or "article" in text or "pricing" in category or "content_angle" in text:
        return "market_trend_article"
    if "google" in text or "profile" in text or "business profile" in text:
        return "manual_profile_observation"
    if "competitor" in category:
        return "competitor_manual_observation"
    return "manual_research"


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
    source_type = clean(raw.get("source_type")) or clean(raw.get("raw_source")) or "unknown"
    evidence_type = infer_evidence_type(raw, category)
    explicit_needs_review = _as_bool(raw.get("needs_review"))
    needs_review_reasons: List[str] = []

    if urgency not in VALID_URGENCIES:
        needs_review_reasons.append(f"invalid urgency={urgency}")
        urgency = "medium"
    if confidence not in VALID_CONFIDENCE:
        needs_review_reasons.append(f"invalid confidence={confidence}")
        confidence = "medium"
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
        "source_type": source_type,
        "evidence_type": evidence_type,
        "source_urls": source_urls,
        "source_timestamp": source_timestamp,
        "tags": split_list(raw.get("tags")),
        "status": status,
        "review_status": review_status,
        "notes": clean(raw.get("notes")),
        "evidence_notes": clean(raw.get("evidence_notes")),
        "client_safe_caveat": clean(raw.get("client_safe_caveat")),
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
