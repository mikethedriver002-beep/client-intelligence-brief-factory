from __future__ import annotations

from typing import Any, Dict, List

URGENCY_SCORE = {"critical": 40, "high": 30, "medium": 18, "low": 8}
CONFIDENCE_SCORE = {"high": 25, "medium": 15, "low": 3}
CATEGORY_BONUS = {
    "competitor_move": 12,
    "opportunity": 12,
    "risk": 10,
    "source_issue": 8,
    "market_signal": 6,
    "industry_update": 4,
}


def score_item(item: Dict[str, Any], client_config: Dict[str, Any]) -> int:
    score = 0
    score += URGENCY_SCORE.get(str(item.get("urgency", "medium")).lower(), 10)
    score += CONFIDENCE_SCORE.get(str(item.get("confidence", "medium")).lower(), 10)
    score += CATEGORY_BONUS.get(str(item.get("category", "")).lower(), 0)
    if item.get("source_urls"):
        score += 10
    if item.get("why_it_matters") and "add analyst" not in item.get("why_it_matters", "").lower():
        score += 10
    if item.get("recommended_action") and "review before" not in item.get("recommended_action", "").lower():
        score += 6
    watch_keywords = [k.lower() for k in client_config.get("watch_keywords", [])]
    haystack = " ".join([item.get("title", ""), item.get("summary", ""), " ".join(item.get("tags", []))]).lower()
    score += min(15, 3 * sum(1 for keyword in watch_keywords if keyword and keyword in haystack))
    if item.get("needs_review"):
        score -= 8
    return max(score, 0)


def rank_items(items: List[Dict[str, Any]], client_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranked = []
    for item in items:
        enriched = dict(item)
        enriched["score"] = score_item(item, client_config)
        ranked.append(enriched)
    return sorted(ranked, key=lambda x: (x["score"], x.get("source_timestamp", "")), reverse=True)
