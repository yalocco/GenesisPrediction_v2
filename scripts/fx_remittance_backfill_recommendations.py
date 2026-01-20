"""
fx_remittance_backfill_recommendations.py

目的:
- 既存の仕送り判断ログ
    data/fx/jpy_thb_remittance_decision_log.csv
  に、recommended_action / recommended_reason を後から一括付与する。

背景:
- fx_remittance_log.py を導入した日以降は recommended_* が入るが、
  過去行は空欄のままになり、summary の action breakdown が薄くなる。
- 本スクリプトは、過去行を含めて推奨行動を埋める。

仕様:
- 各日付 D について、その日の today_row を作り、
  直近 `--recent` 日（デフォルト30日）の過去履歴（Dより前）を参照して
  recommend_action(today_row, recent_df) を計算する。
- 既に recommended_action が入っている行は、デフォルトでは上書きしない。
  上書きしたい場合は --overwrite を付ける。

実行例:
  python scripts/fx_remittance_backfill_recommendations.py
  python scripts/fx_remittance_backfill_recommendations.py --recent 60
  python scripts/fx_remittance_backfill_recommendations.py --overwrite

注意:
- 既存CSVは上書き保存される（安全のため .bak を作成）。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd

# ---- ensure repo root on sys.path ----
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.fx_remittance_recommend import recommend_action


DATA_DIR = REPO_ROOT / "data" / "fx"
DECISION_LOG_PATH = DATA_DIR / "jpy_thb_remittance_decision_log.csv"

REQ_COLS = [
    "date",
    "decision",
    "combined_noise_prob",
    "usd_jpy_noise_prob",
    "usd_thb_noise_prob",
    "remit_note",
]

REC_COLS = ["recommended_action", "recommended_reason"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill recommended_action/reason into remittance decision log.")
    parser.add_argument("--recent", type=int, default=30, help="Lookback window for recommendation (default: 30).")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing recommended_* values.")
    args = parser.parse_args()

    if not DECISION_LOG_PATH.exists():
        raise FileNotFoundError(f"Missing required file: {DECISION_LOG_PATH}")

    df = pd.read_csv(DECISION_LOG_PATH)

    # Validate
    missing = [c for c in REQ_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in log: {missing}")

    # Normalize + sort
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df = df.sort_values("date").reset_index(drop=True)

    # Ensure columns exist
    for c in REC_COLS:
        if c not in df.columns:
            df[c] = ""

    # Backup
    bak_path = DECISION_LOG_PATH.with_suffix(".csv.bak")
    shutil.copy2(DECISION_LOG_PATH, bak_path)

    # Compute
    updated = 0
    for i in range(len(df)):
        if (not args.overwrite) and str(df.at[i, "recommended_action"]).strip():
            continue

        today_row = {
            "date": df.at[i, "date"],
            "decision": df.at[i, "decision"],
            "combined_noise_prob": float(df.at[i, "combined_noise_prob"]),
            "usd_jpy_noise_prob": float(df.at[i, "usd_jpy_noise_prob"]),
            "usd_thb_noise_prob": float(df.at[i, "usd_thb_noise_prob"]),
            "remit_note": df.at[i, "remit_note"],
        }

        # history strictly before i
        start = max(0, i - args.recent)
        hist = df.iloc[start:i].copy()

        if hist.empty:
            recent_df = pd.DataFrame([today_row])
        else:
            recent_df = hist

        action_code, reason = recommend_action(today_row, recent_df)

        df.at[i, "recommended_action"] = action_code
        df.at[i, "recommended_reason"] = reason
        updated += 1

    # Save
    df.to_csv(DECISION_LOG_PATH, index=False, encoding="utf-8")

    print(f"[OK] backfilled recommended_* for {updated} rows")
    print(f"[OK] backup saved: {bak_path}")
    print(f"[OK] updated log:   {DECISION_LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
