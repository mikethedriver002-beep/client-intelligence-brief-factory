# Brief Factory Starter

A clean, brand-neutral starter repo for a white-label agency brief business.

This repo was designed to extract the reusable operating patterns from an active niche-media automation repo without carrying over brand clutter, sports-specific assumptions, assets, or publishing automation.

## What it does

Brief Factory turns source monitoring and manual analyst inputs into a weekly intelligence packet:

1. Audit a client/agency source registry.
2. Ingest manual items and, optionally, public RSS feeds.
3. Normalize everything into `brief_item` contracts.
4. Rank items by urgency, confidence, category, and client relevance.
5. Generate a markdown brief, HTML brief, source appendix CSV, QA report, handoff email, manifest, and ZIP delivery packet.
6. Keep a human-review gate in the loop before anything goes to a client.

## v0.2 status model

Brief Factory now uses three QA statuses:

```text
PASS
PASS_WITH_REVIEW
FAIL
```

Status meanings:

```text
PASS = technically valid and client-ready
PASS_WITH_REVIEW = packet generated, but human review or item review is still required
FAIL = missing required material or source rules failed
```

`delivery_manifest.json` now includes:

```text
qa_status
qa_passed
client_ready
client_ready_warning
fail_count
review_count
needs_review_count
human_review_required
human_review_complete
```

Important: `--strict-qa` only fails the GitHub Actions run when status is `FAIL`. A `PASS_WITH_REVIEW` packet still uploads artifacts so you can inspect and manually approve it.

## What it does not do yet

- No SaaS app
- No user login system
- No payment portal
- No auto-publishing
- No broad data product
- No guarantee of complete market coverage

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_brief_factory.py \
  --client-config config/clients/demo_local_seo_client.json \
  --source-registry config/source_registries/demo_local_seo_sources.json \
  --manual-csv data/inbox/demo_manual_items.csv \
  --run-mode full_delivery_packet \
  --strict-qa
```

Outputs will appear in:

```text
outputs/brief_factory/demo_agency/demo_local_roofing/<run_id>/
```

The ZIP packet will be in:

```text
outputs/brief_factory/demo_agency/demo_local_roofing/<run_id>/delivery_packet.zip
```

## How to run it on GitHub

1. Open the repo on GitHub.
2. Click **Actions**.
3. Click **Brief Factory Run**.
4. Click **Run workflow**.
5. Use these demo values first:

```text
run_mode: full_delivery_packet
client_config: config/clients/demo_local_seo_client.json
source_registry: config/source_registries/demo_local_seo_sources.json
manual_csv: data/inbox/demo_manual_items.csv
enable_network: false
strict_qa: true
```

6. Download the uploaded artifact when the run finishes.

Expected demo result after v0.2:

```text
QA status: PASS_WITH_REVIEW
Client ready: false
Warning: Not client-ready until human review is complete.
```

That is correct. The demo data is meant to produce a reviewable packet, not a finished client packet.

## How to create your first real client packet

Use this flow before outreach or client delivery.

### 1. Copy the pilot client config template

Copy:

```text
config/clients/pilot_local_seo_client.template.json
```

Save it as something like:

```text
config/clients/acme_roofing_local_seo.json
```

Replace the placeholder values:

```text
agency_id
agency_name
client_id
client_name
vertical
brief_period_label
watch_keywords
competitors
service_areas
```

Keep this review posture until you have actually reviewed the packet:

```json
"delivery": {
  "human_review_required": true,
  "human_review_complete": false,
  "review_status": "pending"
}
```

### 2. Copy the pilot source registry template

Copy:

```text
config/source_registries/pilot_local_seo_sources.template.json
```

Save it as something like:

```text
config/source_registries/acme_roofing_sources.json
```

Replace placeholder sources with real public sources:

```text
client website
competitor websites
local event pages
local chamber pages
manual review observations
optional public RSS feeds
```

Every source should include:

```text
source_id
name
source_type
enabled
tier
trust_band
allowed_use
publish_policy
```

### 3. Copy the manual intake template

Copy:

```text
data/inbox/manual_items_template.csv
```

Save it as something like:

```text
data/inbox/acme_roofing_manual_items.csv
```

Replace the sample rows with real signals. Each row should have:

```text
title
summary
why_it_matters
recommended_action
category
urgency
confidence
source_name
source_urls
source_timestamp
status
needs_review
review_status
notes
```

For the first draft, keep:

```text
status: ready_for_review
needs_review: true
review_status: pending
```

After you manually review an item, you can set:

```text
status: operator_verified
needs_review: false
review_status: approved
```

### 4. Run the real packet

Local terminal:

```bash
python scripts/run_brief_factory.py \
  --client-config config/clients/acme_roofing_local_seo.json \
  --source-registry config/source_registries/acme_roofing_sources.json \
  --manual-csv data/inbox/acme_roofing_manual_items.csv \
  --run-mode full_delivery_packet \
  --strict-qa
```

GitHub Actions values:

```text
run_mode: full_delivery_packet
client_config: config/clients/acme_roofing_local_seo.json
source_registry: config/source_registries/acme_roofing_sources.json
manual_csv: data/inbox/acme_roofing_manual_items.csv
enable_network: false
strict_qa: true
```

### 5. Review the artifact

Open these files first:

```text
qa_report.md
delivery_manifest.json
weekly_brief.md
source_appendix.csv
handoff_email.md
```

A `PASS_WITH_REVIEW` packet is still useful. It means the packet generated successfully, but you need to review or approve something before sending it.

### 6. Mark a packet client-ready

Once every item is reviewed and approved, update your files:

Manual CSV rows:

```text
status: operator_verified
needs_review: false
review_status: approved
```

Client config:

```json
"delivery": {
  "human_review_required": true,
  "human_review_complete": true,
  "review_status": "approved"
}
```

Run the workflow again. The target result is:

```text
QA status: PASS
Client ready: true
```

## Recommended first business model

Sell a weekly, human-reviewed, source-backed brief to agencies that already serve clients. Start with one vertical, one client template, and one recurring deliverable.

Suggested package:

```text
White-Label Weekly Client Intelligence Brief
- Top developments
- Opportunities or risks
- Competitor/market signals
- Suggested client actions
- Source appendix
- QA report
- Optional social/talking points
```

## Repo structure

```text
brief_factory/                  Core Python package
config/clients/                 Client and agency configs
config/source_registries/       Trusted source lists by vertical/client
config/templates/               Brief, QA, and email templates
schemas/                        JSON schemas for contracts/configs
scripts/                        CLI runners
workflows/                      Notes for GitHub Actions behavior
.github/workflows/              GitHub Actions runner
data/inbox/                     Manual analyst/client input CSVs
docs/                           Operating docs and build decisions
tests/                          Lightweight tests
outputs/                        Generated files, ignored by git except .gitkeep
```

## Operating posture

Brief Factory is service-first. Use automation to reduce collection and formatting time, not to remove human judgment. Every delivery packet should include source links, timestamps, confidence notes, and a QA report.
