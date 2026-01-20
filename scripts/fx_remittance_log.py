"""
fx_remittance_log.py

目的:
- 今日（または指定日）の JPY→THB 仕送り判断をCSV台帳に記録する
- 推奨行動 recommended_action / recommended_reason を併記する（WARN時の実務判断を軽くする）

出力:
- data/fx/jpy_thb_remittance_decision_log.csv

実行例:
  python scripts/fx_remittance_log.py
  python scripts/fx_remittance_log.py --date 2026-01-20
  python scripts/fx_remittance_log.py --date 2026-01-20 --mode append

モード:
- upsert (default): 同じ date が既にあれば上書き、無ければ追記（安全）
- append: 常に追記（同一日が重複しうる）
"""

from __future__ import annotations

import argparse
import sys
from datetime import date as _date
from pathlib import Path
from typing import Optional

import pandas as pd

# ---- ensure repo root on sys.path ----
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.fx_remittance_recommend import recommend_action


# ---- Paths ----
DATA_DIR = REPO_ROOT / "data" / "fx"

USDJPY_NOISE_PATH = DATA_DIR / "usdjpy_noise_forecast.csv"
USDTHB_NOISE_PATH = DATA_DIR / "usdthb_noise_forecast.csv"
DECISION_LOG_PATH = DATA_DIR / "jpy_thb_remittance_decision_log.csv"

# ---- Thresholds ----
ON_TH = 0.45
WARN_TH = 0.60

# ---- Columns (canonical order) ----
BASE_COLS = [
    "date",
    "decision",
    "combined_noise_prob",
    "usd_jpy_noise_prob",
    "usd_thb_noise_prob",
    "remit_note",
]
NEW_COLS = [
    "recommended_action",
    "recommended_reason",
]
ALL_COLS = BASE_COLS + NEW_COLS


def _read_noise_prob(csv_path: Path, target_date: str) -> float:
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing required file: {csv_path}")

    df = pd.read_csv(csv_path)

    date_cols = [c for c in df.columns if c.lower() in ("date", "ds", "day")]
    if not date_cols:
        date_cols = [df.columns[0]]
    dcol = date_cols[0]
    df[dcol] = pd.to_datetime(df[dcol]).dt.strftime("%Y-%m-%d")

    cand = ["noise_prob", "prob", "p", "noise_probability", "yhat", "yhat_prob"]
    pcol = None
    lower_map = {c.lower(): c for c in df.columns}
    for k in cand:
        if k in lower_map:
            pcol = lower_map[k]
            break
    if pcol is None:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not num_cols:
            raise ValueError(f"No numeric probability column found in {csv_path}")
        pcol = num_cols[-1]

    row = df.loc[df[dcol] == target_date]
    if row.empty:
        row = df.tail(1)

    val = float(row.iloc[0][pcol])
    return max(0.0, min(1.0, val))


def _decision_from_noise(combined_noise_prob: float) -> str:
    if combined_noise_prob < ON_TH:
        return "ON"
    if combined_noise_prob < WARN_TH:
        return "WARN"
    return "OFF"


def _default_note(decision: str) -> str:
    if decision == "ON":
        return "normal"
    if decision == "WARN":
        return "split_or_small"
    return "split_or_wait"


def _load_log() -> Optional[pd.DataFrame]:
    if not DECISION_LOG_PATH.exists():
        return None
    df = pd.read_csv(DECISION_LOG_PATH)

    # normalize date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df.sort_values("date")

    # ensure new cols exist for backward compatibility
    for c in NEW_COLS:
        if c not in df.columns:
            df[c] = ""

    return df.reset_index(drop=True)


def _build_today_row(target_date: str) -> dict:
    usdjpy = _read_noise_prob(USDJPY_NOISE_PATH, target_date)
    usdthb = _read_noise_prob(USDTHB_NOISE_PATH, target_date)
    combined = max(usdjpy, usdthb)

    decision = _decision_from_noise(combined)
    note = _default_note(decision)

    return {
        "date": target_date,
        "decision": decision,
        "combined_noise_prob": combined,
        "usd_jpy_noise_prob": usdjpy,
        "usd_thb_noise_prob": usdthb,
        "remit_note": note,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Append/Upsert today's remittance decision into CSV log.")
    parser.add_argument("--date", default=None, help="Target date (YYYY-MM-DD). Default: today.")
    parser.add_argument("--recent", type=int, default=30, help="Recent days for recommendation (default: 30).")
    parser.add_argument(
        "--mode",
        choices=["upsert", "append"],
        default="upsert",
        help="upsert: overwrite if same date exists; append: always append",
    )
    args = parser.parse_args()

    target_date = args.date or _date.today().strftime("%Y-%m-%d")

    # Load log first (for recommendation context)
    log_df = _load_log()
    if log_df is None:
        recent_df = pd.DataFrame([])
    else:
        recent_df = log_df.tail(args.recent)

    today_row = _build_today_row(target_date)

    # If log is empty, include today itself as minimal context
    if recent_df.empty:
        recent_df = pd.DataFrame([today_row])

    action_code, reason = recommend_action(today_row, recent_df)

    today_row["recommended_action"] = action_code
    today_row["recommended_reason"] = reason

    # Upsert / Append into log_df
    if log_df is None:
        out_df = pd.DataFrame([today_row], columns=ALL_COLS)
    else:
        # Ensure all columns exist and order is stable
        for c in ALL_COLS:
            if c not in log_df.columns:
                log_df[c] = ""

        if args.mode == "append":
            out_df = pd.concat([log_df, pd.DataFrame([today_row])], ignore_index=True)
        else:
            # upsert
            mask = (log_df["date"] == target_date) if "date" in log_df.columns else pd.Series([False] * len(log_df))
            if mask.any():
                idx = log_df.index[mask][0]
                for k, v in today_row.items():
                    log_df.at[idx, k] = v
                out_df = log_df
            else:
                out_df = pd.concat([log_df, pd.DataFrame([today_row])], ignore_index=True)

        # normalize types + sort
        out_df["date"] = pd.to_datetime(out_df["date"]).dt.strftime("%Y-%m-%d")
        out_df = out_df.sort_values("date").reset_index(drop=True)

        # stable column order
        out_df = out_df[[c for c in ALL_COLS if c in out_df.columns] + [c for c in out_df.columns if c not in ALL_COLS]]

    # Write
    DECISION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(DECISION_LOG_PATH, index=False, encoding="utf-8")

    # Print confirmation line
    print(
        f"{target_date} | decision={today_row['decision']} | "
        f"noise={today_row['combined_noise_prob']:.3f} | "
        f"USDJPY={today_row['usd_jpy_noise_prob']:.3f} USDTHB={today_row['usd_thb_noise_prob']:.3f} | "
        f"note={today_row['remit_note']} | "
        f"action={today_row['recommended_action']} | reason={today_row['recommended_reason']} | "
        f"mode={args.mode}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
