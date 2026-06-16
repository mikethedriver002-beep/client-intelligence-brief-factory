from __future__ import annotations

import csv
import json
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

NO_REPLY_STATUSES = {"", "no_reply_yet", "none", "pending"}
NEGATIVE_REPLY_STATUSES = {"not_fit", "not_now", "do_not_contact", "unsubscribed", "closed_lost", "pilot_lost"}
BOUNCE_STATUSES = {"bounced", "bounce"}
FOLLOWUP_DONE_STATUSES = {"sent", "done", "complete", "completed"}


def parse_date(value: str | None) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M %Z", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def norm(value: str | None) -> str:
    return (value or "").strip().lower()


def is_no_reply(row: dict[str, str]) -> bool:
    return norm(row.get("reply_status")) in NO_REPLY_STATUSES


def followup_done(value: str | None) -> bool:
    return norm(value) in FOLLOWUP_DONE_STATUSES


def days_between(start: date | None, end: date) -> int | str:
    if not start:
        return ""
    return max(0, (end - start).days)


def infer_stage(row: dict[str, str], as_of: date) -> str:
    reply_status = norm(row.get("reply_status"))
    status = norm(row.get("status"))
    f1_due = parse_date(row.get("follow_up_1_due"))
    f2_due = parse_date(row.get("follow_up_2_due"))

    if reply_status in BOUNCE_STATUSES:
        return "bounced"
    if reply_status in {"do_not_contact", "unsubscribed"}:
        return "do_not_contact"
    if reply_status in NEGATIVE_REPLY_STATUSES:
        return "closed_lost"
    if reply_status == "pilot_won":
        return "pilot_won"
    if reply_status == "pilot_proposed":
        return "pilot_proposed"
    if reply_status == "sample_delivered":
        return "sample_delivered"
    if reply_status == "sample_requested":
        return "sample_requested"
    if reply_status == "interested":
        return "interested"

    if status == "not_sent":
        return "not_sent"

    if is_no_reply(row):
        if f2_due and f2_due <= as_of and not followup_done(row.get("follow_up_2_status")):
            return "follow_up_2_due"
        if f1_due and f1_due <= as_of and not followup_done(row.get("follow_up_1_status")):
            return "follow_up_1_due"
        if followup_done(row.get("follow_up_2_status")):
            return "follow_up_2_sent"
        if followup_done(row.get("follow_up_1_status")):
            return "follow_up_1_sent"
        return "outreach_sent"

    return "manual_review"


def stage_probability(stage: str) -> int:
    return {
        "not_sent": 0,
        "outreach_sent": 2,
        "follow_up_1_due": 3,
        "follow_up_1_sent": 3,
        "follow_up_2_due": 3,
        "follow_up_2_sent": 2,
        "interested": 20,
        "sample_requested": 35,
        "sample_delivered": 45,
        "pilot_proposed": 60,
        "pilot_won": 100,
        "closed_lost": 0,
        "bounced": 0,
        "do_not_contact": 0,
        "manual_review": 5,
    }.get(stage, 0)


def next_action_for_stage(row: dict[str, str], stage: str) -> str:
    agency = row.get("agency_name", "prospect")
    if stage == "not_sent":
        return f"Send first outreach to {agency}."
    if stage == "outreach_sent":
        return f"Wait for reply. Follow-up 1 due {row.get('follow_up_1_due', '')}."
    if stage == "follow_up_1_due":
        return f"Send Follow-up 1 to {agency}."
    if stage == "follow_up_1_sent":
        return f"Wait for reply. Follow-up 2 due {row.get('follow_up_2_due', '')}."
    if stage == "follow_up_2_due":
        return f"Send Follow-up 2 to {agency}. Then stop unless they reply."
    if stage == "follow_up_2_sent":
        return f"No more cold follow-ups to {agency}. Leave open for reply."
    if stage == "interested":
        return f"Reply with the sample-request intake question for {agency}."
    if stage == "sample_requested":
        return f"Create a custom sample brief config for {agency}."
    if stage == "sample_delivered":
        return f"Ask whether the sample is useful enough to test as a paid pilot."
    if stage == "pilot_proposed":
        return f"Follow up on pilot proposal for {agency}."
    if stage == "pilot_won":
        return f"Move {agency} into delivery/onboarding."
    if stage == "closed_lost":
        return f"Do not continue selling {agency} in this sequence."
    if stage == "bounced":
        return f"Find a better contact route for {agency} or suppress the address."
    if stage == "do_not_contact":
        return f"Suppress {agency} from future outreach."
    return f"Review {agency} manually."


def safe_name(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "prospect"


def make_followup_email(row: dict[str, str], number: int, sender: str) -> str:
    agency = row.get("agency_name", "there")
    subject = row.get("subject", "Brief Factory")
    greeting = f"Hi {agency} team,"
    if number == 1:
        body = f"""{greeting}

Just floating this back up in case it is useful.

The offer is simple: send me one client niche and I will build a small sample Brief Factory packet so your team can judge whether weekly client intelligence briefs are useful for your workflow.

No deck or demo needed. One niche is enough.

Best,
Michael

Brief Factory
White-label client intelligence briefs for agencies
{sender}
"""
    else:
        body = f"""{greeting}

Last note from me. If this is not a fit, no worries.

If client research briefs are useful for any accounts later, the easiest starting point is one client niche, three competitors, and one market. I can turn that into a reviewed sample packet your team can evaluate.

Best,
Michael

Brief Factory
White-label client intelligence briefs for agencies
{sender}
"""
    return f"""To: {row.get('email', '')}
Subject: Re: {subject}

{body.rstrip()}
"""


def build_pipeline_rows(rows: list[dict[str, str]], as_of: date) -> list[dict[str, Any]]:
    pipeline: list[dict[str, Any]] = []
    for row in rows:
        stage = infer_stage(row, as_of)
        sent_date = parse_date(row.get("send_date"))
        pipeline.append({
            "send_order": row.get("send_order", ""),
            "agency_name": row.get("agency_name", ""),
            "email": row.get("email", ""),
            "stage": stage,
            "probability_percent": stage_probability(stage),
            "send_date": row.get("send_date", ""),
            "days_since_sent": days_between(sent_date, as_of),
            "follow_up_1_due": row.get("follow_up_1_due", ""),
            "follow_up_1_status": row.get("follow_up_1_status", ""),
            "follow_up_2_due": row.get("follow_up_2_due", ""),
            "follow_up_2_status": row.get("follow_up_2_status", ""),
            "reply_status": row.get("reply_status", ""),
            "next_action": next_action_for_stage(row, stage),
            "notes": row.get("notes", ""),
        })
    return pipeline


def build_action_rows(pipeline_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {
        "sample_requested": 1,
        "interested": 2,
        "pilot_proposed": 3,
        "follow_up_1_due": 4,
        "follow_up_2_due": 5,
        "not_sent": 6,
        "sample_delivered": 8,
        "manual_review": 9,
        "bounced": 30,
    }
    actions: list[dict[str, Any]] = []
    quiet_stages = {"outreach_sent", "follow_up_1_sent", "follow_up_2_sent", "closed_lost", "do_not_contact", "pilot_won"}
    for row in pipeline_rows:
        stage = str(row.get("stage", ""))
        if stage in quiet_stages:
            continue
        actions.append({
            "priority": priority.get(stage, 99),
            "agency_name": row.get("agency_name", ""),
            "email": row.get("email", ""),
            "stage": stage,
            "action": row.get("next_action", ""),
            "due_date": row.get("follow_up_1_due", "") if stage == "follow_up_1_due" else row.get("follow_up_2_due", "") if stage == "follow_up_2_due" else "",
        })
    return sorted(actions, key=lambda r: (int(r["priority"]), str(r["agency_name"])))


def count_by_stage(pipeline_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in pipeline_rows:
        stage = str(row.get("stage", "unknown"))
        counts[stage] = counts.get(stage, 0) + 1
    return dict(sorted(counts.items()))


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_None._"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines = [header, sep]
    for row in rows:
        vals = [str(row.get(col, "")).replace("\n", " ").replace("|", "/") for col in columns]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_dashboard(output_dir: Path, pipeline_rows: list[dict[str, Any]], action_rows: list[dict[str, Any]], as_of: date, tracker_path: Path) -> None:
    counts = count_by_stage(pipeline_rows)
    sent_total = sum(1 for row in pipeline_rows if row.get("stage") != "not_sent")
    positive_total = sum(1 for row in pipeline_rows if row.get("stage") in {"interested", "sample_requested", "sample_delivered", "pilot_proposed", "pilot_won"})
    due_total = sum(1 for row in pipeline_rows if row.get("stage") in {"follow_up_1_due", "follow_up_2_due"})
    text = [
        "# Brief Factory Sales Ops Control Center",
        "",
        f"Generated as of: `{as_of.isoformat()}`",
        f"Tracker source: `{tracker_path}`",
        "",
        "## Executive summary",
        "",
        f"- Prospects tracked: **{len(pipeline_rows)}**",
        f"- Initial outreach sent: **{sent_total}**",
        f"- Positive reply stages: **{positive_total}**",
        f"- Follow-ups due now: **{due_total}**",
        f"- Actions requiring attention: **{len(action_rows)}**",
        "",
        "## Stage counts",
        "",
        markdown_table([{"stage": k, "count": v} for k, v in counts.items()], ["stage", "count"]),
        "",
        "## Today's action queue",
        "",
        markdown_table(action_rows, ["priority", "agency_name", "email", "stage", "action", "due_date"]),
        "",
        "## Pipeline",
        "",
        markdown_table(pipeline_rows, ["send_order", "agency_name", "email", "stage", "probability_percent", "days_since_sent", "reply_status", "next_action"]),
        "",
        "## Operating rules",
        "",
        "- No attachments on cold follow-ups.",
        "- Stop cold follow-ups after Follow-up 2 unless the prospect replies.",
        "- If a prospect asks for a sample, collect one client niche, geography, competitors, and preferred deliverable format.",
        "- If a prospect says no, not now, or unsubscribe, suppress them from future outreach.",
        "",
    ]
    write_text(output_dir / "SALES_OPS_DASHBOARD.md", "\n".join(text))


def write_todays_actions(output_dir: Path, action_rows: list[dict[str, Any]], as_of: date) -> None:
    lines = ["# Today's Sales Actions", "", f"As of: `{as_of.isoformat()}`", ""]
    if not action_rows:
        lines += [
            "No sales actions are due today.",
            "",
            "If this is a fresh send day, do not force extra outreach. Wait for replies or the next scheduled follow-up date.",
        ]
    else:
        for idx, row in enumerate(action_rows, start=1):
            lines += [
                f"## {idx}. {row.get('agency_name', '')}",
                "",
                f"- Stage: `{row.get('stage', '')}`",
                f"- Email: `{row.get('email', '')}`",
                f"- Action: {row.get('action', '')}",
                f"- Due date: `{row.get('due_date', '')}`",
                "",
            ]
    write_text(output_dir / "TODAYS_SALES_ACTIONS.md", "\n".join(lines))


def write_followups(output_dir: Path, rows: list[dict[str, str]], pipeline_rows: list[dict[str, Any]], sender: str) -> list[dict[str, Any]]:
    by_email = {row.get("email", ""): row for row in rows}
    due: list[dict[str, Any]] = []
    md_sections = ["# Follow-up Emails Due", ""]
    for pipeline in pipeline_rows:
        stage = pipeline.get("stage")
        if stage not in {"follow_up_1_due", "follow_up_2_due"}:
            continue
        source = by_email.get(str(pipeline.get("email", "")), {})
        number = 1 if stage == "follow_up_1_due" else 2
        due_row = {
            "agency_name": source.get("agency_name", ""),
            "email": source.get("email", ""),
            "followup_number": number,
            "subject": f"Re: {source.get('subject', '')}",
            "due_date": pipeline.get("follow_up_1_due", "") if number == 1 else pipeline.get("follow_up_2_due", ""),
        }
        due.append(due_row)
        email_body = make_followup_email(source, number, sender)
        md_sections += [
            f"## {source.get('agency_name', '')} - Follow-up {number}",
            "",
            "```text",
            email_body,
            "```",
            "",
        ]
        filename = f"followup_{number}_{safe_name(source.get('agency_name', 'prospect'))}.txt"
        write_text(output_dir / "followup_emails" / filename, email_body)
    if not due:
        md_sections += ["No follow-up emails are due for this run.", ""]
    write_text(output_dir / "FOLLOWUP_EMAILS_DUE.md", "\n".join(md_sections))
    write_csv(output_dir / "followups_due.csv", due, ["agency_name", "email", "followup_number", "subject", "due_date"])
    return due


def write_reply_router(output_dir: Path, sender: str) -> None:
    text = f"""# Reply Router

Use this when a prospect replies.

## If they say yes / interested

```text
Thanks, happy to build one.

The easiest way to make the sample useful is to send me:

1. One client niche
2. Market or city
3. 2 to 4 competitors or comparison targets
4. Any topic you want watched first
5. Whether you prefer the sample as a PDF, HTML page, or markdown doc

Once I have that, I will build a small reviewed sample brief so you can judge whether the format is useful for your workflow.

Best,
Michael

Brief Factory
White-label client intelligence briefs for agencies
{sender}
```

## If they ask what it costs

```text
For the first pilot, I am keeping it simple:

$500 for one month
one client niche
one weekly reviewed brief
source appendix and client-safe caveats included

If the first month is useful, we can either keep it as a single-client pilot or expand into multiple client niches.

Best,
Michael
```

## If they ask whether this is AI

```text
Good question. I use automation to collect and organize signals, but the deliverable is reviewed before it is sent.

The point is not to dump AI summaries into your workflow. The point is to give your team useful client talking points, source links, caveats, and recommended actions in a format you can actually use.

Best,
Michael
```

## If they say not now

```text
No problem at all. I appreciate the reply.

I will leave you alone for now. If weekly client intelligence briefs become useful later, I am easy to reach here.

Best,
Michael
```

## If they ask to unsubscribe or stop

```text
Understood. I will not contact you again.

Best,
Michael
```
"""
    write_text(output_dir / "REPLY_ROUTER.md", text)


def write_sample_intake(output_dir: Path, pipeline_rows: list[dict[str, Any]]) -> None:
    rows: list[dict[str, Any]] = []
    for row in pipeline_rows:
        if row.get("stage") in {"interested", "sample_requested"}:
            rows.append({
                "agency_name": row.get("agency_name", ""),
                "email": row.get("email", ""),
                "reply_date": "",
                "client_niche": "",
                "market_or_city": "",
                "competitors": "",
                "watch_topics": "",
                "preferred_format": "PDF or HTML",
                "sample_due_date": "",
                "owner": "Michael",
                "status": "intake_needed",
                "notes": "",
            })
    if not rows:
        rows = [{
            "agency_name": "",
            "email": "",
            "reply_date": "",
            "client_niche": "",
            "market_or_city": "",
            "competitors": "",
            "watch_topics": "",
            "preferred_format": "PDF or HTML",
            "sample_due_date": "",
            "owner": "Michael",
            "status": "template",
            "notes": "Copy this row when a prospect asks for a sample.",
        }]
    write_csv(
        output_dir / "sample_request_intake.csv",
        rows,
        ["agency_name", "email", "reply_date", "client_niche", "market_or_city", "competitors", "watch_topics", "preferred_format", "sample_due_date", "owner", "status", "notes"],
    )


def write_stage_guide(output_dir: Path) -> None:
    text = """# Sales Stage Guide

## Status fields

Use `status` for what you did.

```text
not_sent
sent
follow_up_1_sent
follow_up_2_sent
```

Use `reply_status` for what the market did.

```text
no_reply_yet
interested
sample_requested
sample_delivered
pilot_proposed
pilot_won
not_now
not_fit
bounced
do_not_contact
```

## Rules

- Do not attach files to cold emails or cold follow-ups.
- If `reply_status` becomes `interested`, stop cold follow-ups and send the intake question.
- If `reply_status` becomes `sample_requested`, build a custom sample packet.
- If `reply_status` becomes `not_now`, do not push. Park for later.
- If `reply_status` becomes `do_not_contact`, suppress permanently.
- If a message bounces, do not keep emailing that address.
"""
    write_text(output_dir / "SALES_STAGE_GUIDE.md", text)


def zip_outputs(output_dir: Path) -> Path:
    zip_path = output_dir / "sales_ops_control_center_packet.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in output_dir.rglob("*"):
            if path.is_file() and path != zip_path:
                archive.write(path, path.relative_to(output_dir))
    return zip_path


def run_sales_ops_control_center(
    tracker_csv: str | Path,
    output_root: str | Path,
    as_of_date: str | None = None,
    sender: str = "michael@brieffactory.com",
) -> dict[str, Any]:
    tracker_path = Path(tracker_csv)
    if not tracker_path.exists():
        raise FileNotFoundError(f"Missing tracker CSV: {tracker_path}")

    as_of = parse_date(as_of_date) if as_of_date else date.today()
    if as_of is None:
        raise ValueError(f"Invalid as_of_date: {as_of_date}")

    rows = read_csv_rows(tracker_path)
    run_id = f"sales_ops_{as_of.isoformat()}"
    output_dir = Path(output_root) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline_rows = build_pipeline_rows(rows, as_of)
    action_rows = build_action_rows(pipeline_rows)

    write_csv(
        output_dir / "sales_pipeline.csv",
        pipeline_rows,
        ["send_order", "agency_name", "email", "stage", "probability_percent", "send_date", "days_since_sent", "follow_up_1_due", "follow_up_1_status", "follow_up_2_due", "follow_up_2_status", "reply_status", "next_action", "notes"],
    )
    write_csv(output_dir / "todays_sales_actions.csv", action_rows, ["priority", "agency_name", "email", "stage", "action", "due_date"])
    due_followups = write_followups(output_dir, rows, pipeline_rows, sender)
    write_dashboard(output_dir, pipeline_rows, action_rows, as_of, tracker_path)
    write_todays_actions(output_dir, action_rows, as_of)
    write_reply_router(output_dir, sender)
    write_sample_intake(output_dir, pipeline_rows)
    write_stage_guide(output_dir)

    manifest = {
        "schema": "brief_factory.sales_ops_manifest.v1",
        "version": "v0.5",
        "generated_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "as_of_date": as_of.isoformat(),
        "tracker_csv": str(tracker_path),
        "output_dir": str(output_dir),
        "sender": sender,
        "prospects_tracked": len(rows),
        "actions_due": len(action_rows),
        "followups_due": len(due_followups),
        "stage_counts": count_by_stage(pipeline_rows),
        "files": [
            "SALES_OPS_DASHBOARD.md",
            "TODAYS_SALES_ACTIONS.md",
            "sales_pipeline.csv",
            "todays_sales_actions.csv",
            "followups_due.csv",
            "FOLLOWUP_EMAILS_DUE.md",
            "REPLY_ROUTER.md",
            "sample_request_intake.csv",
            "SALES_STAGE_GUIDE.md",
        ],
    }
    write_text(output_dir / "sales_ops_manifest.json", json.dumps(manifest, indent=2))
    zip_path = zip_outputs(output_dir)
    manifest["zip_path"] = str(zip_path)
    write_text(output_dir / "sales_ops_manifest.json", json.dumps(manifest, indent=2))

    return manifest
