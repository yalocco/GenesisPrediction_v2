# scripts/publish_fx_decision_to_analysis.py
# Publish FX decision JSON into data/world_politics/analysis/
#
# Input (default):
#   data/fx/fx_decision_latest.json  (or fx_decision_YYYY-MM-DD.json)
#
# Output:
#   data/world_politics/analysis/fx_decision_latest.json
#   data/world_politics/analysis/fx_decision_YYYY-MM-DD.json
#
# Run:
#   .\.venv\Scripts\python.exe scripts\publish_fx_decision_to_analysis.py --date 2026-01-31
#
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import date as date_cls


SRC_DIR = Path("data/fx")
DST_DIR = Path("data/world_politics/analysis")

SRC_LATEST = SRC_DIR / "fx_decision_latest.json"
DST_LATEST = DST_DIR / "fx_decision_latest.json"


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _save_json(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (default: today)", default=None)
    ap.add_argument("--src", help="source json path (optional)", default=None)
    args = ap.parse_args()

    d = args.date or date_cls.today().isoformat()
    src = Path(args.src) if args.src else (SRC_DIR / f"fx_decision_{d}.json")
    if not src.exists():
        src = SRC_LATEST

    if not src.exists():
        raise SystemExit(f"[ERR] source not found: {src}")

    obj = _load_json(src)

    # Minimal sanity: enforce date field (non-fatal if missing)
    if isinstance(obj, dict):
        obj.setdefault("date", d)

    dst_dated = DST_DIR / f"fx_decision_{d}.json"

    _save_json(DST_LATEST, obj)
    _save_json(dst_dated, obj)

    print("[OK] published FX decision")
    print(f"  src:   {src}")
    print(f"  dst:   {DST_LATEST}")
    print(f"  dated: {dst_dated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
