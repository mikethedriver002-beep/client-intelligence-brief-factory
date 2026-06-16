# Brief Factory v0.5 Sales Ops Control Center

v0.5 turns the sales launch from loose CSV tracking into an operating control center.

## What changed

Added:

```text
brief_factory/sales_ops.py
scripts/run_sales_ops_control_center.py
.github/workflows/sales-ops-control-center.yml
```

The system reads the send-day tracker and generates a sales ops packet.

Default tracker:

```text
sales_launch_kit/contact_enrichment/send_day_tracker_batch_001_2026_06_16.csv
```

Default sender:

```text
michael@brieffactory.com
```

## Generated outputs

A run produces:

```text
SALES_OPS_DASHBOARD.md
todays_sales_actions.csv
TODAYS_SALES_ACTIONS.md
sales_pipeline.csv
followups_due.csv
FOLLOWUP_EMAILS_DUE.md
followup_emails/*.txt
REPLY_ROUTER.md
sample_request_intake.csv
SALES_STAGE_GUIDE.md
sales_ops_manifest.json
sales_ops_control_center_packet.zip
```

## Why it matters

The sales process now has a loop:

```text
send tracker -> sales ops run -> today actions -> follow-ups/reply handling -> update tracker -> run again
```

This prevents the business from becoming random manual outreach.

## Stage model

The engine infers pipeline stages from `status`, `reply_status`, and follow-up dates.

Core stages:

```text
not_sent
outreach_sent
follow_up_1_due
follow_up_1_sent
follow_up_2_due
follow_up_2_sent
interested
sample_requested
sample_delivered
pilot_proposed
pilot_won
closed_lost
bounced
do_not_contact
```

## Daily workflow

Run the workflow every morning while outreach is active.

1. Open GitHub Actions.
2. Run **Sales Ops Control Center**.
3. Use the default tracker unless a new batch tracker exists.
4. For normal daily use, leave `as_of_date` blank.
5. For testing follow-up day, set `as_of_date` manually.

Example follow-up test date:

```text
2026-06-19
```

## Follow-up rules

The output generates follow-up copy only when due.

Rules:

```text
No attachments.
Plain text only.
Stop after Follow-up 2 unless they reply.
Suppress unsubscribes and bounces.
If interested, stop the cold sequence and switch to intake.
```

## When someone replies yes

Use:

```text
REPLY_ROUTER.md
sample_request_intake.csv
```

The intake asks for:

```text
1. One client niche
2. Market or city
3. 2 to 4 competitors
4. First watch topic
5. Preferred format
```

Once intake is complete, build a custom sample brief using the main Brief Factory packet workflow.

## First success metric

For Batch 001, the goal is not a sale on the first email.

The first success metric is:

```text
1 interested reply
```

The second success metric is:

```text
1 sample requested
```

The first monetization target is:

```text
1 paid pilot at $500 for one month
```

## No paid dependencies

v0.5 uses only Python standard-library modules.

No paid APIs.
No CRM subscription.
No email automation tool.
No scraping proxy.
No SaaS dashboard.
