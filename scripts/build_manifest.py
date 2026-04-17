"""
Build a manifest.json for the corridor-data repo from the current data/ state.

Emits JSON on stdout so it can be redirected:

    python scripts/build_manifest.py > ../corridor-data/manifest.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    # Honor CORRIDOR_DATA_ROOT the same way the runtime does.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.shared.pipeline.utils import DATA_DIR

    freshness_path = DATA_DIR / "freshness.json"
    if not freshness_path.exists():
        print(f"ERROR: no freshness.json at {freshness_path}", file=sys.stderr)
        return 1

    freshness = json.loads(freshness_path.read_text())
    manifest = {
        "version": "v1",
        "description": "Abidjan-Lagos Corridor Intelligence Platform - snapshot manifest",
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "bucket": "r2://corridor-data/v1",
        "pipelines": {},
    }

    for name, info in freshness.items():
        if isinstance(info, dict):
            manifest["pipelines"][name] = {
                "pulled_at": info.get("pulled_at"),
                "records": info.get("records"),
            }

    json.dump(manifest, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
