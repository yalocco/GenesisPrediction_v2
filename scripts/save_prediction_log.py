# scripts/save_prediction_log.py
# Trend3 FX 永続化ログ保存（正式版）
#
# 目的:
# - trend3_fx_latest.json を読み込む
# - メタ情報を付加して prediction_log_YYYY-MM-DD.json として保存
# - 将来の再計算不要な研究資産として凍結
#
# Run:
#   .venv\Scripts\python.exe scripts\save_prediction_log.py \
#       --date 2026-02-19 \
#       --prediction-json analysis/prediction_backtests/trend3_fx_latest.json \
#       --out analysis/prediction_logs/prediction_log_2026-02-19.json
#
# 設計思想:
# - 元JSONは改変しない
# - meta.persisted を追加
# - source_file / repo info を明示
# - 壊れたJSONは保存しない（exit 2）

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


# -----------------------------
# Utilities
# -----------------------------
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def build_persist_meta(
    source_path: Path,
    run_date: str,
) -> Dict[str, Any]:
    return {
        "persisted_at_utc": utc_now_iso(),
        "run_date_utc": run_date,
        "source_file": str(source_path),
        "schema_version": 1,
        "note": "Frozen prediction log (do not modify retrospectively).",
    }


# -----------------------------
# Main
# -----------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="UTC date YYYY-MM-DD")
    ap.add_argument("--prediction-json", required=True, help="Path to latest prediction JSON")
    ap.add_argument("--out", required=True, help="Output frozen log path")
    args = ap.parse_args()

    source_path = Path(args.prediction_json).resolve()
    out_path = Path(args.out).resolve()
    run_date = args.date

    if not source_path.exists():
        print(f"[ERROR] prediction JSON not found: {source_path}")
        return 2

    try:
        data = load_json(source_path)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        return 2

    # --- Validation ---
    if "summary" not in data or "details" not in data:
        print("[ERROR] Invalid prediction JSON structure (missing summary/details)")
        return 2

    # --- Add persist meta ---
    persist_meta = build_persist_meta(source_path, run_date)

    # Preserve original meta
    if "meta" not in data:
        data["meta"] = {}

    data["meta"]["persist"] = persist_meta

    # --- Write ---
    try:
        write_json(out_path, data)
    except Exception as e:
        print(f"[ERROR] Failed to write output: {e}")
        return 2

    print("[OK] persisted prediction log:")
    print(f"  source: {source_path}")
    print(f"  out   : {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())