#!/usr/bin/env python3
"""
Publish daily_summary artifacts (dated + latest) from analyzer summary.json.

- src   : data/world_politics/analysis/summary.json
- dated : data/world_politics/analysis/daily_summary_YYYY-MM-DD.json
- latest: data/world_politics/analysis/daily_summary_latest.json

Rationale:
- build_data_health expects daily_summary_latest.json freshness.
- normalize step can only pick from existing daily_summary_YYYY-MM-DD.json files.
  If those are missing, it falls back to an old date (e.g., 2026-02-22).
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "world_politics" / "analysis"


def _validate_date(s: str) -> str:
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError as e:
        raise SystemExit(f"[ERROR] invalid --date '{s}' (expected YYYY-MM-DD)") from e
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, type=_validate_date, help="YYYY-MM-DD (target publish date)")
    args = ap.parse_args()

    src = ANALYSIS_DIR / "summary.json"
    if not src.exists():
        raise SystemExit(f"[ERROR] missing source: {src}")

    # sanity check: must be JSON
    try:
        with src.open("r", encoding="utf-8") as f:
            json.load(f)
    except Exception as e:
        raise SystemExit(f"[ERROR] source is not valid JSON: {src}") from e

    dated = ANALYSIS_DIR / f"daily_summary_{args.date}.json"
    latest = ANALYSIS_DIR / "daily_summary_latest.json"

    dated.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dated)
    shutil.copyfile(dated, latest)

    print("[OK] published daily_summary_latest")
    print(f"  src   : {src}")
    print(f"  dated : {dated}")
    print(f"  latest: {latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())