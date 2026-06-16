from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

import requests

from .utils import clean, now_utc, stable_id


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value or "")


def _first_text(element: ET.Element, names: List[str]) -> str:
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return clean(_strip_html(found.text))
    return ""


def fetch_rss_items(source: Dict[str, Any], timeout_seconds: int = 10, max_items: int = 10) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    source_id = clean(source.get("source_id"))
    source_name = clean(source.get("name")) or source_id
    for url in source.get("urls") or []:
        response = requests.get(url, timeout=timeout_seconds, headers={"User-Agent": "BriefFactory/0.1 (+human-reviewed)"})
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
        for entry in items[:max_items]:
            title = _first_text(entry, ["title", "{http://www.w3.org/2005/Atom}title"])
            summary = _first_text(entry, ["description", "summary", "{http://www.w3.org/2005/Atom}summary"])
            link = _first_text(entry, ["link"])
            if not link:
                atom_link = entry.find("{http://www.w3.org/2005/Atom}link")
                if atom_link is not None:
                    link = clean(atom_link.attrib.get("href"))
            published = _first_text(entry, ["pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"])
            out.append({
                "raw_source": "rss",
                "item_id": stable_id("rss", source_id, title, link),
                "title": title,
                "summary": summary,
                "why_it_matters": "Needs analyst interpretation before client delivery.",
                "recommended_action": "Review and decide whether to include.",
                "category": "industry_update",
                "urgency": "medium",
                "confidence": "medium",
                "status": "needs_review",
                "source_id": source_id,
                "source_name": source_name,
                "source_urls": [link] if link else [url],
                "source_timestamp": published or now_utc(),
                "tags": source.get("client_relevance", []),
                "notes": "Fetched from RSS. Human review required.",
            })
    return out


def ingest_enabled_rss_sources(registry: Dict[str, Any], enable_network: bool = False) -> List[Dict[str, Any]]:
    if not enable_network:
        return []
    items: List[Dict[str, Any]] = []
    for source in registry.get("sources", []):
        if not isinstance(source, dict):
            continue
        if not source.get("enabled") or source.get("source_type") != "rss":
            continue
        if source.get("requires_login") or source.get("resale_restricted"):
            continue
        try:
            items.extend(fetch_rss_items(source))
        except Exception as exc:
            items.append({
                "raw_source": "rss_error",
                "item_id": stable_id("rss_error", source.get("source_id"), str(exc)),
                "title": f"RSS fetch failed: {clean(source.get('name') or source.get('source_id'))}",
                "summary": str(exc),
                "why_it_matters": "Source failed and should be checked before client delivery.",
                "recommended_action": "Fix source or mark unavailable.",
                "category": "source_issue",
                "urgency": "high",
                "confidence": "high",
                "status": "needs_review",
                "source_id": source.get("source_id"),
                "source_name": source.get("name"),
                "source_urls": source.get("urls", []),
                "source_timestamp": now_utc(),
                "tags": ["source_failure"],
                "notes": str(exc),
            })
    return items
