# Brief Factory v0.3 Pilot Polish

v0.3 upgrades the generated packet from a technically correct brief into a stronger sales and delivery package.

## What changed

1. Suggested talking points now use a clean signal-to-action format.
2. `weekly_brief.md` now opens with an Executive Summary written like an agency action memo.
3. `weekly_brief.md` now includes a Source Quality section.
4. Each top item now includes an Evidence note.
5. Each top item now includes a Client-safe caveat.
6. Every run now generates `outreach_ready_sample.md` and `outreach_ready_sample.html`.
7. Every run now generates `agency_sales_sample.md` and `agency_sales_sample.html`.
8. `source_appendix.csv` now includes `source_id`, `category`, `urgency`, `evidence_notes`, and `client_safe_caveat` columns.
9. `handoff_email.md` now lists the new outreach and sales sample files.

## New output files

Every full delivery packet should now include:

```text
weekly_brief.md
weekly_brief.html
outreach_ready_sample.md
outreach_ready_sample.html
agency_sales_sample.md
agency_sales_sample.html
source_appendix.csv
qa_report.md
qa_report.json
normalized_items.json
delivery_manifest.json
delivery_packet.zip
```

## Toronto roofing pilot run settings

Use these GitHub Actions values:

```text
run_mode: full_delivery_packet
client_config: config/clients/pilot_toronto_roofing_local_seo.json
source_registry: config/source_registries/pilot_toronto_roofing_sources.json
manual_csv: data/inbox/pilot_toronto_roofing_manual_items.csv
enable_network: false
strict_qa: true
```

Expected result:

```text
QA status: PASS
Client ready: true
```

## What to inspect after the run

Open these files first:

```text
weekly_brief.md
outreach_ready_sample.md
agency_sales_sample.md
source_appendix.csv
qa_report.md
delivery_manifest.json
```

The main quality check is whether the brief feels like an agency could send or adapt it for a client conversation, not just whether the code ran.
