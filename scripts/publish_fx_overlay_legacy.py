#!/usr/bin/env python3
"""
Publish legacy FX overlay filename expected by Data Health.

Your pipeline already generates:
  data/world_politics/analysis/fx_jpy_thb_overlay_YYYY-MM-DD.png

But health expects:
  data/world_politics/analysis/fx_overlay_YYYY-MM-DD.png

This script copies fx_jpy_thb_overlay_YYYY-MM-DD.png -> fx_overlay_YYYY-MM-DD.png
without touching SST logic (purely derived artifact).
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


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
    ap.add_argument("--date", required=True, type=_validate_date, help="YYYY-MM-DD")
    args = ap.parse_args()

    src = ANALYSIS_DIR / f"fx_jpy_thb_overlay_{args.date}.png"
    dst = ANALYSIS_DIR / f"fx_overlay_{args.date}.png"

    if not src.exists():
        raise SystemExit(f"[ERROR] missing source overlay: {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

    print("[OK] published legacy fx_overlay")
    print(f"  src: {src}")
    print(f"  dst: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())