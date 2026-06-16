from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Iterable


def build_zip(output_dir: Path, zip_name: str = "delivery_packet.zip", include_patterns: Iterable[str] | None = None) -> Path:
    include_patterns = list(include_patterns or ["*.md", "*.html", "*.csv", "*.json"])
    zip_path = output_dir / zip_name
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for pattern in include_patterns:
            for path in output_dir.glob(pattern):
                if path.name == zip_path.name:
                    continue
                archive.write(path, path.name)
    return zip_path
