from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_prediction_shape(pred: Any) -> Dict[str, Any]:
    """
    Normalize prediction JSON into the structure expected by prediction_log writer.

    Expected structure:
      {
        "summary": {...},
        "details": {... or [...]},
        ... (optional)
      }

    If incoming JSON already has summary/details, keep it.
    Otherwise wrap it:
      summary: minimal auto-generated summary
      details: the original JSON (full-fidelity)
    """
    if isinstance(pred, dict) and ("summary" in pred and "details" in pred):
        # Already in expected structure
        return pred

    # Auto-summary heuristics (best-effort, schema-agnostic)
    summary: Dict[str, Any] = {
        "generated": True,
        "generated_at_utc": utc_now_iso(),
        "note": "Auto-wrapped prediction JSON (original schema preserved under details).",
        "keys_top_level": sorted(list(pred.keys())) if isinstance(pred, dict) else None,
    }

    # Common backtest fields (if present)
    if isinstance(pred, dict):
        for k in ["calls", "hit", "miss", "hit_rate", "win_rate", "accuracy"]:
            if k in pred:
                summary[k] = pred.get(k)

        # Sometimes nested summary-ish payloads exist
        for k in ["result", "metrics", "stats", "summary"]:
            if k in pred and isinstance(pred.get(k), (dict, list)):
                summary["hint_has_" + k] = True

    return {
        "summary": summary,
        "details": pred,
    }


def build_log_record(date_utc: str, prediction: Dict[str, Any], source_path: str) -> Dict[str, Any]:
    return {
        "date_utc": date_utc,
        "created_at_utc": utc_now_iso(),
        "source_prediction_json": source_path,
        "prediction": prediction,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Save daily prediction log (schema-tolerant).")
    parser.add_argument("--date", required=True, help="UTC date YYYY-MM-DD")
    parser.add_argument("--prediction-json", required=True, help="Path to prediction JSON (latest)")
    parser.add_argument("--out", required=True, help="Output path for daily prediction log JSON")
    args = parser.parse_args()

    pred_path = Path(args.prediction_json)
    if not pred_path.exists():
        print(f"[ERROR] prediction json not found: {pred_path}")
        return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    raw_pred = load_json(pred_path)
    normalized = ensure_prediction_shape(raw_pred)

    record = build_log_record(args.date, normalized, str(pred_path))

    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] wrote prediction log: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())