from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .utils import clean, read_csv, split_list, stable_id


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
        items.append({
            "raw_source": "manual_csv",
            "item_id": item_id,
            "title": title,
            "summary": summary,
            "why_it_matters": clean(row.get("why_it_matters")),
            "recommended_action": clean(row.get("recommended_action")),
            "category": clean(row.get("category")) or "market_signal",
            "urgency": clean(row.get("urgency")) or "medium",
            "confidence": clean(row.get("confidence")) or "medium",
            "status": clean(row.get("status")) or "ready_for_review",
            "source_name": clean(row.get("source_name")),
            "source_urls": source_urls,
            "source_timestamp": clean(row.get("source_timestamp") or row.get("published_at")),
            "tags": split_list(row.get("tags")),
            "notes": clean(row.get("notes")),
        })
    return items
