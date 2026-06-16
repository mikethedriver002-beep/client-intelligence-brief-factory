# Contact Enrichment and Sales Tracking

This folder holds the operational sales records for Brief Factory outreach.

## Current batch

```text
email_verified_send_batch_001_2026_06_16.csv
send_day_tracker_batch_001_2026_06_16.csv
```

## How to use the tracker

Update `send_day_tracker_batch_001_2026_06_16.csv` when anything changes.

Use `status` for what Michael did:

```text
not_sent
sent
follow_up_1_sent
follow_up_2_sent
```

Use `reply_status` for what the prospect did:

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

## Batch 001 status

Batch 001 was sent from:

```text
michael@brieffactory.com
```

Sent prospects:

```text
Page Pros
Local SEO Search
Reputation.ca
NKPR
BrandLume
```

Follow-up 1 due:

```text
2026-06-19
```

Follow-up 2 due:

```text
2026-06-23
```

## Next step

Run the **Sales Ops Control Center** workflow to generate:

```text
SALES_OPS_DASHBOARD.md
TODAYS_SALES_ACTIONS.md
FOLLOWUP_EMAILS_DUE.md
REPLY_ROUTER.md
sample_request_intake.csv
sales_pipeline.csv
```
