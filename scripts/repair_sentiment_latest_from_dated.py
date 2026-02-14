# scripts/repair_sentiment_latest_from_dated.py
# Repair data/world_politics/analysis/sentiment_latest.json by replacing it
# with the dated sentiment_<date>.json that matches its (base_)date.
#
# Why:
# - Sometimes sentiment_latest.json can end up with stale items while date is updated.
# - This script forces consistency: latest == dated file for the same date.
#
# Usage:
#   .\.venv\Scripts\python.exe scripts\repair_sentiment_latest_from_dated.py
#   .\.venv\Scripts\python.exe scripts\repair_sentiment_latest_from_dated.py --date 2026-02-14

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "world_politics" / "analysis"
LATEST = ANALYSIS / "sentiment_latest.json"


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def pick_date(doc: dict) -> str:
    for k in ("base_date", "date"):
        v = doc.get(k)
        if isinstance(v, str) and v:
            return v
    raise ValueError("sentiment_latest.json has no base_date/date")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="force date YYYY-MM-DD (optional)")
    args = ap.parse_args()

    if not LATEST.exists():
        print(f"[ERR] missing: {LATEST}")
        return 2

    cur = load_json(LATEST)
    date = args.date or pick_date(cur)

    dated = ANALYSIS / f"sentiment_{date}.json"
    if not dated.exists():
        # fallback: newest dated file
        candidates = sorted(ANALYSIS.glob("sentiment_*.json"))
        if not candidates:
            print(f"[ERR] no dated sentiment_*.json under {ANALYSIS}")
            return 2
        newest = max(candidates, key=lambda p: p.stat().st_mtime)
        print(f"[WARN] dated file not found for {date}. Using newest: {newest.name}")
        dated = newest

    src = load_json(dated)

    # backup latest
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = LATEST.with_suffix(f".json.bak_{ts}")
    shutil.copy2(LATEST, bak)

    # overwrite latest with dated
    LATEST.write_text(json.dumps(src, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[OK] repaired sentiment_latest.json from dated file")
    print(f"     BACKUP: {bak} ({bak.stat().st_size} bytes)")
    print(f"     SRC   : {dated} ({dated.stat().st_size} bytes)")
    print(f"     DST   : {LATEST} ({LATEST.stat().st_size} bytes)")

    # quick sanity: show first 3 urls
    items = src.get("items") if isinstance(src, dict) else None
    if isinstance(items, list) and items:
        print("     sample urls:")
        for it in items[:3]:
            if isinstance(it, dict):
                print("       -", it.get("url"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
