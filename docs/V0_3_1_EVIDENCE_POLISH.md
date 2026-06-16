# Brief Factory v0.3.1 Evidence Polish

v0.3.1 fixes evidence metadata and caveat logic so the sales packet is safer and more professional.

## Fixes shipped

1. `manual_ingest.py` now preserves `source_id` from the manual CSV.
2. Manual rows now carry `source_type`, `evidence_type`, `evidence_notes`, and `client_safe_caveat` through the pipeline.
3. `normalizer.py` now stores `source_type` and `evidence_type` in `normalized_items.json`.
4. `quality_gate.py` now flags missing `source_id`, `source_type`, or `evidence_type` on top items.
5. `render.py` now uses `evidence_type` for caveats instead of treating every manual CSV row as a manual profile observation.
6. Market trend article items now get market-trend caveats.
7. Event/watch items now get event verification caveats.
8. Manual profile observations now keep the stricter profile-recheck caveat.
9. `source_appendix.csv` now includes `source_type` and `evidence_type` columns.
10. `output_validation.py` now validates required output files and required evidence columns after rendering.
11. `run_brief_factory.py` now writes `output_validation` into `delivery_manifest.json`.
12. The GitHub Action strict mode now fails on true QA failures or true output-validation failures.

## Evidence types used now

```text
manual_profile_observation
competitor_manual_observation
market_trend_article
event_watch
rss_discovery
manual_research
```

## Expected Toronto pilot result

Run values:

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
Output validation: PASS
```

## What to inspect

Open these files in the artifact:

```text
delivery_manifest.json
normalized_items.json
source_appendix.csv
weekly_brief.md
outreach_ready_sample.md
agency_sales_sample.md
```

Confirm:

```text
source_id is populated
evidence_type is populated
article items use market-trend caveats
event items use event-watch caveats
manual profile items use profile-recheck caveats
output_validation.status is PASS
```
