# Build Decision: New Repo, Not HSD Subfolder

## Decision

Build Brief Factory as a new, brand-neutral repository.

## Why

The HSD repo is an active production/workflow space for a specific sports media brand. Adding a commercial agency product directly to it would create confusion across naming, configs, workflows, outputs, secrets, content assumptions, and generated artifacts.

Brief Factory should inherit only the reusable patterns:

- Source registries and trust bands
- Source audit reports
- Manual inbox intake
- Contract normalization
- Ranking and readiness scoring
- Human-review quality gates
- Delivery packets and ZIPs
- GitHub Actions orchestration

It should not inherit:

- HSD branding
- sports-only fields
- player/team/image asset logic
- graphics pipeline logic
- social-platform queues unless later added as a paid add-on
- HSD run histories or generated outputs

## Migration posture

This is not a fork. It is a clean-room product skeleton inspired by working patterns in the donor repo.

## First commercial target

White-label weekly intelligence briefs for agencies with one client vertical and one client template.
