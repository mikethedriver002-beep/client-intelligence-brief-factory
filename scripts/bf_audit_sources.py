#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brief_factory.source_audit import audit_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a Brief Factory source registry")
    parser.add_argument("--source-registry", default="config/source_registries/demo_local_seo_sources.json")
    parser.add_argument("--output-dir", default="outputs/brief_factory/source_audit")
    args = parser.parse_args()
    audit, _rows = audit_registry(Path(args.source_registry), Path(args.output_dir))
    print(audit)
    return 0 if audit["counts"]["fail"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
