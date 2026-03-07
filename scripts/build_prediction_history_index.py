#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GenesisPrediction v2
Prediction History Index Builder

Purpose:
- Read prediction history snapshots
- Build a lightweight prediction_history_index.json
- Provide a stable UI-friendly history source

Input:
- analysis/prediction/history/YYYY-MM-DD/prediction.json

Output:
- analysis/prediction/prediction_history_index.json
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis"
PREDICTION_DIR = ANALYSIS_DIR / "prediction"
HISTORY_DIR = PREDICTION_DIR / "history"
INDEX_PATH = PREDICTION_DIR / "prediction_history_index.json"


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or isinstance(value, bool):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_entry(date_str: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    probs = payload.get("scenario_probabilities", {})
    meta = payload.get("meta", {}) if isinstance(payload.get("meta"), dict) else {}

    return {
        "date": date_str,
        "as_of": payload.get("as_of", date_str),
        "generated_at": payload.get("generated_at"),
        "horizon": payload.get("horizon", "7d"),
        "overall_risk": payload.get("overall_risk"),
        "confidence": round(safe_float(payload.get("confidence")), 4),
        "dominant_scenario": payload.get("dominant_scenario"),
        "best_case": round(safe_float(probs.get("best_case")), 4),
        "base_case": round(safe_float(probs.get("base_case")), 4),
        "worst_case": round(safe_float(probs.get("worst_case")), 4),
        "summary": payload.get("summary"),
        "watchpoints": payload.get("watchpoints", []) if isinstance(payload.get("watchpoints"), list) else [],
        "drivers": payload.get("drivers", []) if isinstance(payload.get("drivers"), list) else [],
        "invalidation_conditions": (
            payload.get("invalidation_conditions", [])
            if isinstance(payload.get("invalidation_conditions"), list)
            else []
        ),
        "signal_count": int(safe_float(meta.get("signal_count"), 0)),
    }


def list_history_dates() -> List[Path]:
    if not HISTORY_DIR.exists():
        return []
    return sorted(
        [
            p for p in HISTORY_DIR.iterdir()
            if p.is_dir() and p.name and len(p.name) == 10
        ],
        key=lambda p: p.name
    )


def build_index(limit: Optional[int] = None) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    date_dirs = list_history_dates()

    for date_dir in date_dirs:
        prediction_path = date_dir / "prediction.json"
        if not prediction_path.exists():
            continue

        try:
            payload = load_json(prediction_path)
        except Exception:
            continue

        if not isinstance(payload, dict):
            continue

        rows.append(normalize_entry(date_dir.name, payload))

    if limit is not None and limit > 0:
        rows = rows[-limit:]

    latest = rows[-1] if rows else None

    return {
        "generated_at": utc_now_iso(),
        "root": str(HISTORY_DIR.relative_to(ROOT)).replace("\\", "/"),
        "count": len(rows),
        "latest_date": latest["date"] if latest else None,
        "items": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build prediction history index.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Keep only the latest N history rows in the index",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not HISTORY_DIR.exists():
        print(f"[PredictionIndex] WARN: history dir not found: {HISTORY_DIR}")
        payload = {
            "generated_at": utc_now_iso(),
            "root": str(HISTORY_DIR.relative_to(ROOT)).replace("\\", "/"),
            "count": 0,
            "latest_date": None,
            "items": [],
        }
        write_json(INDEX_PATH, payload)
        print(f"[PredictionIndex] OK: wrote empty index -> {INDEX_PATH}")
        return 0

    payload = build_index(limit=args.limit)
    write_json(INDEX_PATH, payload)

    print(f"[PredictionIndex] OK: wrote -> {INDEX_PATH}")
    print(f"[PredictionIndex] count={payload['count']} latest_date={payload['latest_date']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())