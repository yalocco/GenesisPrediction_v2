"""
fx_remittance_today.py

目的:
- 今日のJPY→THB仕送り判断 (ON/WARN/OFF) を表示する
- 推奨行動 (recommended_action) と理由 (recommended_reason) を表示する

注意:
- Windows / venv / 直接実行でも import が壊れないように
  sys.path に repo root を追加してから import する
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

# ---- ensure repo root on sys.path ----
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ---- safe import ----
from scripts.fx_remittance_recommend import recommend_action


# ---- Paths ----
DATA_DIR = REPO_ROOT / "data" / "fx"

USDJPY_NOISE_PATH = DATA_DIR / "usdjpy_noise_forecast.csv"
USDTHB_NOISE_PATH = DATA_DIR / "usdthb_noise_forecast.csv"
DECISION_LOG_PATH = DATA_DIR / "jpy_thb_remittance_decision_log.csv"

# ---- Thresholds ----
ON_TH = 0.45
WARN_TH = 0.60


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


def _load_recent_log(n_recent: int = 30) -> Optional[pd.DataFrame]:
    if not DECISION_LOG_PATH.exists():
        return None
    df = pd.read_csv(DECISION_LOG_PATH)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df.sort_values("date")
    return df.tail(n_recent).reset_index(drop=True)


def build_today_row(target_date: str) -> dict:
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
    parser = argparse.ArgumentParser(description="Show today's JPY→THB remittance decision with recommendation.")
    parser.add_argument("--date", default=None, help="Target date (YYYY-MM-DD). Default: today.")
    parser.add_argument("--recent", type=int, default=30, help="Recent days for recommendation (default: 30).")
    args = parser.parse_args()

    target_date = args.date or date.today().strftime("%Y-%m-%d")

    today_row = build_today_row(target_date)

    recent_df = _load_recent_log(args.recent)
    if recent_df is None:
        recent_df = pd.DataFrame([today_row])

    action_code, reason = recommend_action(today_row, recent_df)

    print(
        f"{today_row['date']} | decision={today_row['decision']} | "
        f"noise={today_row['combined_noise_prob']:.3f} | "
        f"USDJPY={today_row['usd_jpy_noise_prob']:.3f} USDTHB={today_row['usd_thb_noise_prob']:.3f} | "
        f"note={today_row['remit_note']} | "
        f"action={action_code} | reason={reason}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
