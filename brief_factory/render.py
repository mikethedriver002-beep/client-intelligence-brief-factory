from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .utils import ensure_dir, markdown_to_basic_html, now_utc, write_csv, write_json

SOURCE_FIELDS = ["rank", "item_id", "title", "source_name", "source_url", "source_timestamp", "confidence", "needs_review"]


def _qa_status(qa_report: Dict[str, Any]) -> str:
    if qa_report.get("status"):
        return str(qa_report["status"])
    return "PASS" if qa_report.get("passed") else "FAIL"


def _client_ready_label(qa_report: Dict[str, Any]) -> str:
    return "Yes" if qa_report.get("client_ready") else "No"


def render_brief_markdown(client_config: Dict[str, Any], items: List[Dict[str, Any]], qa_report: Dict[str, Any]) -> str:
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
        lines += [
            "## Client-readiness warning",
            "",
            warning,
            "",
        ]

    lines += [
        "## What changed this week",
        "",
    ]
    if top_items:
        first_titles = "; ".join(item["title"] for item in top_items[:3])
        lines.append(f"The highest-priority signals this week are: {first_titles}.")
    else:
        lines.append("No client-ready items were found. Review sources and manual intake.")

    lines += ["", "## Top developments", ""]
    for index, item in enumerate(top_items, start=1):
        source_note = item.get("source_urls", [""])[0] if item.get("source_urls") else "Source needed"
        review_note = " Needs review." if item.get("needs_review") else ""
        lines += [
            f"### {index}. {item['title']}",
            "",
            f"**Summary:** {item.get('summary', '')}",
            "",
            f"**Why it matters:** {item.get('why_it_matters', '')}",
            "",
            f"**Recommended action:** {item.get('recommended_action', '')}",
            "",
            f"**Category / urgency / confidence:** {item.get('category')} / {item.get('urgency')} / {item.get('confidence')}.{review_note}",
            "",
            f"**Source:** {source_note}",
            "",
        ]

    lines += ["## Watch list", ""]
    if watch_items:
        for item in watch_items:
            lines.append(f"- **{item['title']}** - {item.get('summary', '')}")
    else:
        lines.append("No secondary watch items this run.")

    lines += [
        "",
        "## Suggested talking points",
        "",
    ]
    for item in top_items[:3]:
        lines.append(f"- {item.get('recommended_action', 'Review item')}: {item['title']}")

    lines += [
        "",
        "## Source appendix",
        "",
        "See `source_appendix.csv` for source URLs, timestamps, and confidence notes.",
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


def render_source_appendix(output_dir: Path, items: List[Dict[str, Any]]) -> None:
    rows = []
    for rank, item in enumerate(items, start=1):
        urls = item.get("source_urls") or [""]
        for url in urls:
            rows.append({
                "rank": rank,
                "item_id": item.get("item_id", ""),
                "title": item.get("title", ""),
                "source_name": item.get("source_name", ""),
                "source_url": url,
                "source_timestamp": item.get("source_timestamp", ""),
                "confidence": item.get("confidence", ""),
                "needs_review": "Yes" if item.get("needs_review") else "No",
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
- source_appendix.csv
- qa_report.md
- normalized_items.json
- delivery_manifest.json

Please review any QA notes before forwarding to the client.
"""


def write_delivery_files(output_dir: Path, client_config: Dict[str, Any], items: List[Dict[str, Any]], qa_report: Dict[str, Any], manifest: Dict[str, Any]) -> None:
    ensure_dir(output_dir)
    markdown = render_brief_markdown(client_config, items, qa_report)
    (output_dir / "weekly_brief.md").write_text(markdown, encoding="utf-8")
    html = markdown_to_basic_html(markdown, f"Weekly Brief - {client_config.get('client_name', 'Client')}")
    (output_dir / "weekly_brief.html").write_text(html, encoding="utf-8")
    render_source_appendix(output_dir, items)
    (output_dir / "qa_report.md").write_text(render_qa_markdown(qa_report), encoding="utf-8")
    (output_dir / "handoff_email.md").write_text(render_handoff_email(client_config, items, qa_report), encoding="utf-8")
    write_json(output_dir / "normalized_items.json", {"items": items})
    write_json(output_dir / "qa_report.json", qa_report)
    write_json(output_dir / "delivery_manifest.json", manifest)
