# Donor Repo Map

This file explains which HSD repo patterns were extracted into Brief Factory.

| Donor repo pattern | Brief Factory equivalent |
|---|---|
| `config/source_registry.json` trust bands | `config/source_registries/*.json` |
| `generate_hsd_source_registry_audit_v2.py` | `brief_factory/source_audit.py` |
| `operator/inbox/manual_workflow_inbox.csv` | `data/inbox/*.csv` |
| `content_packet.json` generation | `brief_item` contracts in `normalized_items.json` |
| `manual_workflow_handoff_packs/*.zip` | `delivery_packet.zip` |
| pipeline review artifact | source audit + QA report + delivery manifest |
| GitHub Actions run modes | `brief-factory-run.yml` |

## Important change

The new repo removes HSD-specific sports, graphics, asset, and publishing assumptions. It is built around agency/client intelligence briefs.
