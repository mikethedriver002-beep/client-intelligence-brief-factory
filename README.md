# Brief Factory Starter

A clean, brand-neutral starter repo for a white-label agency brief business.

This repo was designed to extract the reusable operating patterns from an active niche-media automation repo without carrying over brand clutter, sports-specific assumptions, assets, or publishing automation.

## What it does

Brief Factory turns public-source monitoring and manual analyst inputs into a client-ready weekly intelligence packet:

1. Audit a client/agency source registry.
2. Ingest manual items and, optionally, public RSS feeds.
3. Normalize everything into `brief_item` contracts.
4. Rank items by urgency, confidence, category, and client relevance.
5. Generate a markdown brief, HTML brief, source appendix CSV, QA report, handoff email, manifest, and ZIP delivery packet.
6. Keep a human-review gate in the loop before anything goes to a client.

## What it does not do yet

- No SaaS app
- No login system
- No payment portal
- No auto-publishing
- No proprietary data resale
- No scraping of login-gated/paywalled sources
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
  --run-mode full_delivery_packet
```

Outputs will appear in:

```text
outputs/brief_factory/demo_agency/demo_local_roofing/<run_id>/
```

The ZIP packet will be in:

```text
outputs/brief_factory/demo_agency/demo_local_roofing/<run_id>/delivery_packet.zip
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
