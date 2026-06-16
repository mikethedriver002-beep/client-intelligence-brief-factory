from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .utils import ensure_dir, markdown_to_basic_html, now_utc, write_csv, write_json

SOURCE_FIELDS = [
    "rank",
    "item_id",
    "title",
    "category",
    "urgency",
    "source_id",
    "source_type",
    "evidence_type",
    "source_name",
    "source_url",
    "source_timestamp",
    "confidence",
    "needs_review",
    "evidence_notes",
    "client_safe_caveat",
]

PROFILE_EVIDENCE_TYPES = {"manual_profile_observation", "competitor_manual_observation"}
MARKET_EVIDENCE_TYPES = {"market_trend_article"}
EVENT_EVIDENCE_TYPES = {"event_watch"}
RSS_EVIDENCE_TYPES = {"rss_discovery"}


def _qa_status(qa_report: Dict[str, Any]) -> str:
    return str(qa_report.get("status") or ("PASS" if qa_report.get("passed") else "FAIL"))


def _client_ready_label(qa_report: Dict[str, Any]) -> str:
    return "Yes" if qa_report.get("client_ready") else "No"


def _first_source_url(item: Dict[str, Any]) -> str:
    urls = item.get("source_urls") or []
    return urls[0] if urls else "Source needed"


def _is_manual_observation(item: Dict[str, Any]) -> bool:
    evidence_type = str(item.get("evidence_type") or "").lower()
    if evidence_type in PROFILE_EVIDENCE_TYPES:
        return True
    if evidence_type:
        return False
    text = " ".join(str(item.get(key, "")) for key in ["source_name", "source_id"]).lower()
    return "profile" in text or "business profile" in text or "google" in text


def _evidence_note(item: Dict[str, Any]) -> str:
    override = str(item.get("evidence_notes") or "").strip()
    if override:
        return override
    source_name = item.get("source_name") or "Source"
    source_date = item.get("source_timestamp") or "date not supplied"
    notes = item.get("notes") or "Source link included in source appendix."
    return f"{source_name}; checked {source_date}. {notes}"


def _client_safe_caveat(item: Dict[str, Any]) -> str:
    override = str(item.get("client_safe_caveat") or "").strip()
    if override:
        return override
    if item.get("needs_review"):
        return "Do not send this item to a client until the listed review reasons are resolved."

    evidence_type = str(item.get("evidence_type") or "").lower()
    if evidence_type in PROFILE_EVIDENCE_TYPES or _is_manual_observation(item):
        return "Manual profile observation. Recheck the live profile before quoting exact ratings, review counts, hours, or service claims externally."
    if evidence_type in MARKET_EVIDENCE_TYPES:
        return "Market trend source. Use as directional context and pair with client-specific data before making a final recommendation."
    if evidence_type in EVENT_EVIDENCE_TYPES:
        return "Event watch item. Verify official vendor, sponsorship, deadline, and cost details before pitching action to the client."
    if evidence_type in RSS_EVIDENCE_TYPES:
        return "RSS discovery item. Confirm against the linked source before including in a client-ready recommendation."
    if item.get("confidence") == "medium":
        return "Use as directional context and pair with client-specific evidence before final recommendations."
    if item.get("confidence") == "low":
        return "Use as a watch item only until stronger confirmation is available."
    return "Client-safe for an internal strategy brief when summarized with source link and timestamp."


def _source_quality_lines(manifest: Dict[str, Any] | None, qa_report: Dict[str, Any], items: List[Dict[str, Any]]) -> List[str]:
    manifest = manifest or {}
    source_audit = manifest.get("source_audit", {}) if isinstance(manifest.get("source_audit", {}), dict) else {}
    counts = source_audit.get("counts", {}) if isinstance(source_audit.get("counts", {}), dict) else {}
    manual_count = sum(1 for item in items if _is_manual_observation(item))
    market_count = sum(1 for item in items if str(item.get("evidence_type") or "").lower() in MARKET_EVIDENCE_TYPES)
    event_count = sum(1 for item in items if str(item.get("evidence_type") or "").lower() in EVENT_EVIDENCE_TYPES)
    missing_source_id = sum(1 for item in items if not item.get("source_id"))
    lines = [
        "## Source Quality",
        "",
        f"- Source audit: {counts.get('pass', 0)} passed, {counts.get('review', 0)} need review, {counts.get('fail', 0)} failed.",
        f"- Trust mix: {counts.get('green', 0)} green, {counts.get('yellow', 0)} yellow, {counts.get('red', 0)} red.",
        f"- Item QA: {qa_report.get('fail_count', 0)} fail, {qa_report.get('review_count', 0)} review, {qa_report.get('needs_review_count', 0)} needs-review items.",
        f"- Evidence mix: {manual_count} manual profile observations, {market_count} market trend sources, {event_count} event/watch items.",
        f"- Missing source_id values: {missing_source_id}.",
    ]
    if manual_count:
        lines.append("- Manual profile caveat: recheck live profile details before quoting exact ratings, review counts, hours, or service claims externally.")
    if market_count:
        lines.append("- Market trend caveat: treat trend articles as directional context, not client-specific proof.")
    if event_count:
        lines.append("- Event watch caveat: verify official event/vendor details before recommending a sponsorship or booth action.")
    lines.append("- Delivery posture: client-ready for internal strategy use." if qa_report.get("client_ready") else "- Delivery posture: not client-ready until QA and review issues are resolved.")
    return lines + [""]


def _executive_summary_lines(client_config: Dict[str, Any], items: List[Dict[str, Any]]) -> List[str]:
    agency_name = client_config.get("agency_name", client_config.get("agency_id", "Agency"))
    client_name = client_config.get("client_name", client_config.get("client_id", "Client"))
    top_items = items[:3]
    categories = {str(item.get("category", "")).lower() for item in items}

    if not items:
        return ["## Executive Summary", "", "No usable signals were found in this run. Review the source registry and manual intake before sending a brief.", ""]

    if any("competitor" in category for category in categories):
        strategic_frame = "competitor positioning and reputation pressure"
    elif any("market" in category for category in categories):
        strategic_frame = "market demand and content strategy"
    else:
        strategic_frame = "client-relevant market movement"

    lines = [
        "## Executive Summary",
        "",
        f"This week's brief for {client_name} points to {strategic_frame}. The value for {agency_name} is a short action memo the team can use to improve local visibility, tighten client messaging, and identify the next practical move.",
        "",
        "Recommended agency priority:",
        "",
    ]
    for index, item in enumerate(top_items, start=1):
        lines.append(f"{index}. **{item['title']}:** {item.get('recommended_action', 'Review this item before delivery.')}")
    lines += ["", "Bottom line: treat the highest-priority items as action prompts, not passive news clips.", ""]
    return lines


def _item_block(index: int, item: Dict[str, Any]) -> List[str]:
    review_note = " Needs review." if item.get("needs_review") else ""
    return [
        f"### {index}. {item['title']}",
        "",
        f"**Summary:** {item.get('summary', '')}",
        "",
        f"**Why it matters:** {item.get('why_it_matters', '')}",
        "",
        f"**Recommended action:** {item.get('recommended_action', '')}",
        "",
        f"**Evidence note:** {_evidence_note(item)}",
        "",
        f"**Client-safe caveat:** {_client_safe_caveat(item)}",
        "",
        f"**Evidence type:** {item.get('evidence_type') or 'unknown'}",
        "",
        f"**Category / urgency / confidence:** {item.get('category')} / {item.get('urgency')} / {item.get('confidence')}.{review_note}",
        "",
        f"**Source:** {_first_source_url(item)}",
        "",
    ]


def _talking_point(item: Dict[str, Any]) -> str:
    return f"- **{item.get('title', 'Brief item')}:** {item.get('recommended_action') or 'Review this signal and decide whether it should become a client action.'}"


def render_brief_markdown(client_config: Dict[str, Any], items: List[Dict[str, Any]], qa_report: Dict[str, Any], manifest: Dict[str, Any] | None = None) -> str:
    top_count = int(client_config.get("quality", {}).get("top_count", 5))
    top_items = items[:top_count]
    watch_items = items[top_count: top_count + 5]
    client_name = client_config.get("client_name", client_config.get("client_id", "Client"))
    agency_name = client_config.get("agency_name", client_config.get("agency_id", "Agency"))
    period = client_config.get("brief_period_label", "This week")
    qa_status = _qa_status(qa_report)
    warning = qa_report.get("warning")

    lines = [
        f"# Weekly Intelligence Brief: {client_name}",
        "",
        f"Prepared for: {agency_name}",
        f"Period: {period}",
        f"Generated: {now_utc()}",
        f"QA status: {qa_status}",
        f"Client ready: {_client_ready_label(qa_report)}",
        "",
    ]
    if warning:
        lines += ["## Client-readiness warning", "", warning, ""]

    lines += _executive_summary_lines(client_config, items)
    lines += _source_quality_lines(manifest, qa_report, items)

    lines += ["## Top developments", ""]
    for index, item in enumerate(top_items, start=1):
        lines += _item_block(index, item)

    lines += ["## Watch list", ""]
    if watch_items:
        for item in watch_items:
            lines.append(f"- **{item['title']}** - {item.get('summary', '')}")
    else:
        lines.append("No secondary watch items this run.")

    lines += ["", "## Suggested talking points", ""]
    if top_items:
        for item in top_items[:5]:
            lines.append(_talking_point(item))
    else:
        lines.append("- No talking points generated because no ranked items were available.")

    lines += ["", "## Client-safe caveats", ""]
    caveats: List[str] = []
    for item in top_items:
        caveat = _client_safe_caveat(item)
        if caveat not in caveats:
            caveats.append(caveat)
    for caveat in caveats:
        lines.append(f"- {caveat}")

    lines += [
        "",
        "## Source appendix",
        "",
        "See `source_appendix.csv` for source URLs, timestamps, confidence notes, evidence types, evidence notes, and client-safe caveats.",
        "",
        "## QA notes",
        "",
        f"Status: {qa_status}",
        f"Client ready: {_client_ready_label(qa_report)}",
        f"Fail count: {qa_report.get('fail_count')}",
        f"Review count: {qa_report.get('review_count')}",
        f"Needs-review item count: {qa_report.get('needs_review_count')}",
        "",
    ]
    if qa_report.get("issues"):
        for issue in qa_report["issues"]:
            lines.append(f"- **{issue['severity'].upper()}** | {issue['item_id']} | {issue['issue']}")
    else:
        lines.append("No QA issues detected.")

    return "\n".join(lines) + "\n"


def render_outreach_ready_sample(client_config: Dict[str, Any], items: List[Dict[str, Any]], qa_report: Dict[str, Any], manifest: Dict[str, Any] | None = None) -> str:
    client_name = client_config.get("client_name", "Sample Client")
    agency_name = client_config.get("agency_name", "Agency")
    lines = [
        f"# Outreach-Ready Sample Brief: {client_name}",
        "",
        f"Prepared as a sample packet for {agency_name}",
        f"QA status: {_qa_status(qa_report)}",
        f"Client ready: {_client_ready_label(qa_report)}",
        "",
        "## What this sample proves",
        "",
        "This sample shows how a weekly agency brief can turn monitoring into client-ready actions. Each item includes a plain-English signal, why it matters, recommended action, evidence note, evidence type, and caveat.",
        "",
        "## Three signals an agency could act on this week",
        "",
    ]
    for index, item in enumerate(items[:3], start=1):
        lines += [
            f"### {index}. {item['title']}",
            "",
            f"**What happened:** {item.get('summary', '')}",
            "",
            f"**Why the client should care:** {item.get('why_it_matters', '')}",
            "",
            f"**Agency action:** {item.get('recommended_action', '')}",
            "",
            f"**Evidence note:** {_evidence_note(item)}",
            "",
            f"**Evidence type:** {item.get('evidence_type') or 'unknown'}",
            "",
            f"**Client-safe caveat:** {_client_safe_caveat(item)}",
            "",
        ]
    lines += ["## Source quality snapshot", ""]
    lines += [line for line in _source_quality_lines(manifest, qa_report, items) if not line.startswith("##")]
    lines += [
        "## How to use this sample in sales",
        "",
        "- Send it as a proof-of-concept to agencies that already sell SEO, PR, content, reputation, or client reporting retainers.",
        "- Position it as a weekly client intelligence layer, not a generic automation tool.",
        "- Offer to build one custom sample for one real client niche before selling a monthly retainer.",
        "",
    ]
    return "\n".join(lines) + "\n"


def render_agency_sales_sample(client_config: Dict[str, Any], items: List[Dict[str, Any]], qa_report: Dict[str, Any], manifest: Dict[str, Any] | None = None) -> str:
    agency_name = client_config.get("agency_name", "Agency")
    client_name = client_config.get("client_name", "Sample Client")
    vertical = client_config.get("vertical", "client intelligence")
    source_audit = (manifest or {}).get("source_audit", {}) if isinstance((manifest or {}).get("source_audit", {}), dict) else {}
    counts = source_audit.get("counts", {}) if isinstance(source_audit.get("counts", {}), dict) else {}
    lines = [
        "# One-Page Agency Sales Sample",
        "",
        "## Offer",
        "",
        "White-label weekly client intelligence briefs for agencies that want better reporting, sharper client conversations, and more action-ready insights without hiring another researcher.",
        "",
        "## Sample context",
        "",
        f"- Agency: {agency_name}",
        f"- Sample client: {client_name}",
        f"- Vertical: {vertical}",
        f"- QA status: {_qa_status(qa_report)}",
        f"- Client ready: {_client_ready_label(qa_report)}",
        "",
        "## What this sample found",
        "",
    ]
    for item in items[:3]:
        lines.append(f"- {item.get('title', 'Signal')}")
    lines += [
        "",
        "## What the agency receives every week",
        "",
        "- Executive memo with the week's highest-priority client signals",
        "- Ranked developments with why-it-matters notes",
        "- Recommended client actions and talking points",
        "- Evidence notes, source links, timestamps, evidence types, and source appendix",
        "- QA report and client-readiness status",
        "- Delivery ZIP that can be reviewed, edited, and forwarded",
        "",
        "## Why agencies buy this",
        "",
        "- Saves research and reporting time",
        "- Creates better client check-in conversations",
        "- Turns monitoring into concrete client actions",
        "- Helps agencies add a premium reporting layer to existing retainers",
        "",
        "## Quality snapshot",
        "",
        f"- Sources checked: {counts.get('sources', 0)}",
        f"- Source failures: {counts.get('fail', 0)}",
        f"- QA fail count: {qa_report.get('fail_count', 0)}",
        f"- QA review count: {qa_report.get('review_count', 0)}",
        "",
        "## Suggested pilot package",
        "",
        "Start with one agency, one client niche, one weekly brief, and one month of delivery. Price the first pilot as a paid proof-of-concept, then convert to a monthly white-label retainer.",
        "",
    ]
    return "\n".join(lines) + "\n"


def render_source_appendix(output_dir: Path, items: List[Dict[str, Any]]) -> None:
    rows = []
    for rank, item in enumerate(items, start=1):
        urls = item.get("source_urls") or [""]
        for url in urls:
            rows.append({
                "rank": rank,
                "item_id": item.get("item_id", ""),
                "title": item.get("title", ""),
                "category": item.get("category", ""),
                "urgency": item.get("urgency", ""),
                "source_id": item.get("source_id", ""),
                "source_type": item.get("source_type", ""),
                "evidence_type": item.get("evidence_type", ""),
                "source_name": item.get("source_name", ""),
                "source_url": url,
                "source_timestamp": item.get("source_timestamp", ""),
                "confidence": item.get("confidence", ""),
                "needs_review": "Yes" if item.get("needs_review") else "No",
                "evidence_notes": _evidence_note(item),
                "client_safe_caveat": _client_safe_caveat(item),
            })
    write_csv(output_dir / "source_appendix.csv", rows, SOURCE_FIELDS)


def render_qa_markdown(qa_report: Dict[str, Any]) -> str:
    qa_status = _qa_status(qa_report)
    lines = [
        "# QA Report",
        "",
        f"Status: {qa_status}",
        f"Passed technical QA: {'Yes' if qa_report.get('passed') else 'No'}",
        f"Client ready: {_client_ready_label(qa_report)}",
        f"Warning: {qa_report.get('warning') or 'None'}",
        f"Items checked: {qa_report.get('items_checked')}",
        f"Fail count: {qa_report.get('fail_count')}",
        f"Review count: {qa_report.get('review_count')}",
        f"Needs-review item count: {qa_report.get('needs_review_count')}",
        f"Human review required: {'Yes' if qa_report.get('human_review_required') else 'No'}",
        f"Human review complete: {'Yes' if qa_report.get('human_review_complete') else 'No'}",
        "",
        "## Issues",
        "",
    ]
    if qa_report.get("issues"):
        for issue in qa_report["issues"]:
            lines.append(f"- **{issue['severity'].upper()}** | {issue['item_id']} | {issue['issue']}")
    else:
        lines.append("No QA issues detected.")
    return "\n".join(lines) + "\n"


def render_handoff_email(client_config: Dict[str, Any], items: List[Dict[str, Any]], qa_report: Dict[str, Any]) -> str:
    client_name = client_config.get("client_name", "client")
    agency_name = client_config.get("agency_name", "team")
    qa_status = _qa_status(qa_report)
    client_ready = bool(qa_report.get("client_ready"))
    status = "client-ready" if client_ready else "not client-ready until human review is complete"
    warning = qa_report.get("warning") or "No client-readiness warning."
    top_titles = "\n".join(f"- {item['title']}" for item in items[:3]) or "- No top items"
    return f"""Subject: Weekly Intelligence Brief for {client_name}

Hi {agency_name},

Your weekly intelligence brief for {client_name} is ready for review.

QA status: {qa_status}
Client ready: {'Yes' if client_ready else 'No'}
Packet status: {status}
Warning: {warning}

Top items:
{top_titles}

Included in this packet:
- weekly_brief.md
- weekly_brief.html
- outreach_ready_sample.md
- outreach_ready_sample.html
- agency_sales_sample.md
- agency_sales_sample.html
- source_appendix.csv
- qa_report.md
- normalized_items.json
- delivery_manifest.json

Please review any QA notes before forwarding to the client.
"""


def write_delivery_files(output_dir: Path, client_config: Dict[str, Any], items: List[Dict[str, Any]], qa_report: Dict[str, Any], manifest: Dict[str, Any]) -> None:
    ensure_dir(output_dir)

    markdown = render_brief_markdown(client_config, items, qa_report, manifest)
    (output_dir / "weekly_brief.md").write_text(markdown, encoding="utf-8")
    (output_dir / "weekly_brief.html").write_text(markdown_to_basic_html(markdown, f"Weekly Brief - {client_config.get('client_name', 'Client')}"), encoding="utf-8")

    outreach = render_outreach_ready_sample(client_config, items, qa_report, manifest)
    (output_dir / "outreach_ready_sample.md").write_text(outreach, encoding="utf-8")
    (output_dir / "outreach_ready_sample.html").write_text(markdown_to_basic_html(outreach, "Outreach Ready Sample"), encoding="utf-8")

    sales_sample = render_agency_sales_sample(client_config, items, qa_report, manifest)
    (output_dir / "agency_sales_sample.md").write_text(sales_sample, encoding="utf-8")
    (output_dir / "agency_sales_sample.html").write_text(markdown_to_basic_html(sales_sample, "Agency Sales Sample"), encoding="utf-8")

    render_source_appendix(output_dir, items)
    (output_dir / "qa_report.md").write_text(render_qa_markdown(qa_report), encoding="utf-8")
    (output_dir / "handoff_email.md").write_text(render_handoff_email(client_config, items, qa_report), encoding="utf-8")
    write_json(output_dir / "normalized_items.json", {"items": items})
    write_json(output_dir / "qa_report.json", qa_report)
    write_json(output_dir / "delivery_manifest.json", manifest)
