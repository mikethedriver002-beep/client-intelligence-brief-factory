from brief_factory.quality_gate import run_quality_gate


def test_quality_gate_passes_three_sourced_items():
    items = []
    for index in range(3):
        items.append({
            "item_id": f"item-{index}",
            "title": f"Item {index}",
            "summary": "Summary",
            "why_it_matters": "It matters.",
            "recommended_action": "Act.",
            "confidence": "high",
            "source_urls": ["https://example.com"],
            "source_timestamp": "2026-06-16",
            "needs_review": False,
        })
    report = run_quality_gate(items, {"quality": {"minimum_items": 3, "top_count": 3}}, {"counts": {"fail": 0}})
    assert report["passed"] is True


def test_quality_gate_fails_missing_sources():
    items = [{
        "item_id": "item-1",
        "title": "Item",
        "summary": "Summary",
        "why_it_matters": "It matters.",
        "recommended_action": "Act.",
        "confidence": "high",
        "source_urls": [],
        "source_timestamp": "2026-06-16",
        "needs_review": False,
    }]
    report = run_quality_gate(items, {"quality": {"minimum_items": 1, "top_count": 1}}, {"counts": {"fail": 0}})
    assert report["passed"] is False
