# Brief Factory v0.4 Sales Launch Kit

v0.4 adds the first go-to-market package for selling Brief Factory as a service-first agency product.

## What v0.4 adds

```text
sales_launch_kit/01_cold_outreach_email.md
sales_launch_kit/02_linkedin_dm.md
sales_launch_kit/03_agency_pitch_one_pager.md
sales_launch_kit/04_pricing_packages.md
sales_launch_kit/05_onboarding_questionnaire.md
sales_launch_kit/06_sample_brief_offer.md
sales_launch_kit/07_prospect_target_list_structure.md
sales_launch_kit/08_objection_handling.md
sales_launch_kit/09_sales_process_sop.md
sales_launch_kit/prospect_target_list_template.csv
scripts/generate_sales_launch_kit.py
.github/workflows/sales-launch-kit.yml
```

## Positioning

Brief Factory should be sold first as a white-label client intelligence brief service for agencies.

Do not sell SaaS yet.

The first offer:

```text
Send me one client niche and I will build a sample weekly intelligence brief your agency can review.
```

## First buyer profile

Start with agencies that already sell monthly retainers:

```text
local SEO agencies
reputation management agencies
PR firms
content marketing agencies
fractional CMO shops
small B2B marketing agencies
```

## First sales goal

```text
Close one paid pilot: one agency, one client niche, one weekly brief, one month.
```

Suggested first pilot price:

```text
$500/month
```

## GitHub Action

Run the `Sales Launch Kit` workflow.

Input:

```text
output_root: outputs/sales_launch_kit
```

Expected artifact:

```text
brief-factory-v0-4-sales-launch-kit-<run_number>
```

Expected generated ZIP:

```text
outputs/sales_launch_kit/brief_factory_v0_4_sales_launch_kit/brief_factory_v0_4_sales_launch_kit.zip
```

## How to use the generated kit

1. Read `SALES_LAUNCH_KIT_INDEX.md`.
2. Use `prospect_target_list_template.csv` to build the first 25 prospect list.
3. Send the cold email or LinkedIn DM to the top 10 prospects.
4. Offer one sample client brief.
5. Use the onboarding questionnaire after a prospect replies.
6. Generate a custom sample brief.
7. Ask for a one-month paid pilot.
