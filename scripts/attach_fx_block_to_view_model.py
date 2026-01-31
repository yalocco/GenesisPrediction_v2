# scripts/attach_fx_block_to_view_model.py
# Attach fx_block to Digest ViewModel JSON (post-process step).
#
# Reads:
#   data/digest/view/{date}.json  (or legacy digest_view_model_{date}.json)
#   data/world_politics/analysis/fx_decision_{date}.json (fallback: fx_decision_latest.json)
#
# Writes (in-place):
#   data/digest/view/{date}.json  (same file updated with viewmodel["fx_block"])
#
# Run:
#   .\.venv\Scripts\python.exe scripts\attach_fx_block_to_view_model.py --date 2026-01-31
#
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import date as date_cls
from typing import Any, Dict


ROOT = Path(__file__).resolve().parent.parent

VIEWMODEL_DIR = ROOT / "data" / "digest" / "view"
ANALYSIS_DIR = ROOT / "data" / "world_politics" / "analysis"


def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _save_json(p: Path, obj: Dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _view_model_path_by_date(date_str: str) -> Path | None:
    p1 = VIEWMODEL_DIR / f"{date_str}.json"
    if p1.exists():
        return p1
    p2 = VIEWMODEL_DIR / f"digest_view_model_{date_str}.json"  # legacy
    if p2.exists():
        return p2
    return None


def _fx_decision_path_by_date(date_str: str) -> Path | None:
    p1 = ANALYSIS_DIR / f"fx_decision_{date_str}.json"
    if p1.exists():
        return p1
    p2 = ANALYSIS_DIR / "fx_decision_latest.json"
    if p2.exists():
        return p2
    return None


def _normalize_fx_block(date_str: str, fx_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize various FX decision json shapes into ViewModel fx_block.
    """
    return {
        "date": date_str,
        "decision": fx_obj.get("fx_decision") or fx_obj.get("decision"),
        "confidence": fx_obj.get("confidence"),
        "fx_reasons": fx_obj.get("fx_reasons", []) if isinstance(fx_obj.get("fx_reasons", []), list) else [],
        "reference": fx_obj.get("analyzer_reference", fx_obj.get("reference", []))
        if isinstance(fx_obj.get("analyzer_reference", fx_obj.get("reference", [])), list) else [],
        "watchlist": fx_obj.get("watchlist", []) if isinstance(fx_obj.get("watchlist", []), list) else [],
        "disclaimer": fx_obj.get("disclaimer"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (default: today)", default=None)
    ap.add_argument("--dry-run", action="store_true", help="do not write file, only print result")
    args = ap.parse_args()

    date_str = args.date or date_cls.today().isoformat()

    vm_path = _view_model_path_by_date(date_str)
    if not vm_path:
        raise SystemExit(f"[ERR] view_model not found for date={date_str} under: {VIEWMODEL_DIR}")

    fx_path = _fx_decision_path_by_date(date_str)
    if not fx_path:
        print(f"[SKIP] fx_decision not found for date={date_str} under: {ANALYSIS_DIR}")
        return 0

    vm = _load_json(vm_path)
    fx = _load_json(fx_path)

    vm["fx_block"] = _normalize_fx_block(date_str, fx)

    if args.dry_run:
        print("[DRY] would write fx_block into view_model")
        print(f"  view_model: {vm_path}")
        print(f"  fx_decision: {fx_path}")
        print(json.dumps(vm["fx_block"], ensure_ascii=False, indent=2))
        return 0

    _save_json(vm_path, vm)
    print("[OK] attached fx_block to view_model")
    print(f"  view_model: {vm_path}")
    print(f"  fx_decision: {fx_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
