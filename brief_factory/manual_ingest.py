from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .utils import clean, read_csv, split_list, stable_id


def infer_evidence_type(row: Dict[str, Any]) -> str:
    """Infer a stable evidence type for manual rows.

    This keeps downstream caveats from treating every CSV row as the same kind of
    evidence. A manually entered market article is not the same as a manual
    profile observation.
    """

    explicit = clean(row.get("evidence_type"))
    if explicit:
        return explicit

    category = clean(row.get("category")).lower()
    source_id = clean(row.get("source_id")).lower()
    source_name = clean(row.get("source_name")).lower()
    text = " ".join([category, source_id, source_name])

    if "event" in category or "opportunity" in category or "event" in text or "cne" in text or "chamber" in text:
        return "event_watch"
    if "market" in category or "trend" in text or "article" in text or "content_angle" in text or "pricing" in category:
        return "market_trend_article"
    if "google" in text or "profile" in text or "business profile" in text or "manual_observation" in text:
        return "manual_profile_observation"
    if "competitor" in category:
        return "competitor_manual_observation"
    return "manual_research"


def ingest_manual_csv(path: Path) -> List[Dict[str, Any]]:
    rows = read_csv(path)
    items: List[Dict[str, Any]] = []
    for row in rows:
        if not any(clean(value) for value in row.values()):
            continue
        title = clean(row.get("title") or row.get("headline") or row.get("item_title"))
        summary = clean(row.get("summary") or row.get("description"))
        source_urls = split_list(row.get("source_urls") or row.get("source_url") or row.get("url"))
        item_id = clean(row.get("item_id")) or stable_id("manual", title, summary, ";".join(source_urls))
        evidence_type = infer_evidence_type(row)
        items.append({
            "raw_source": clean(row.get("raw_source")) or "manual_csv",
            "item_id": item_id,
            "title": title,
            "summary": summary,
            "why_it_matters": clean(row.get("why_it_matters")),
            "recommended_action": clean(row.get("recommended_action")),
            "category": clean(row.get("category")) or "market_signal",
            "urgency": clean(row.get("urgency")) or "medium",
            "confidence": clean(row.get("confidence")) or "medium",
            "status": clean(row.get("status")) or "ready_for_review",
            "review_status": clean(row.get("review_status")),
            "needs_review": clean(row.get("needs_review")),
            "source_id": clean(row.get("source_id")),
            "source_name": clean(row.get("source_name")),
            "source_type": clean(row.get("source_type")) or "manual",
            "evidence_type": evidence_type,
            "source_urls": source_urls,
            "source_timestamp": clean(row.get("source_timestamp") or row.get("published_at")),
            "tags": split_list(row.get("tags")),
            "notes": clean(row.get("notes")),
            "evidence_notes": clean(row.get("evidence_notes")),
            "client_safe_caveat": clean(row.get("client_safe_caveat")),
        })
    return items
