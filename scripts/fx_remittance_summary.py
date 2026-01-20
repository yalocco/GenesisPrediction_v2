"""
fx_remittance_summary.py

目的:
- JPY→THB 仕送り判断ログ（CSV）を集計して、運用判断に役立つサマリーを表示する
- 直近N日サマリー（従来機能）に加えて、月次レポート --month を提供する

入力:
- data/fx/jpy_thb_remittance_decision_log.csv

出力:
- 標準出力（ターミナル表示）

実行例:
  # 直近30日（デフォルト）
  python scripts/fx_remittance_summary.py

  # 直近60日
  python scripts/fx_remittance_summary.py --days 60

  # 月次（YYYY-MM）
  python scripts/fx_remittance_summary.py --month 2026-01

  # 月次（当月・ローカル日付基準）
  python scripts/fx_remittance_summary.py --month
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd


# ---- Paths ----
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "fx"
DECISION_LOG_PATH = DATA_DIR / "jpy_thb_remittance_decision_log.csv"

# ---- Columns ----
REQ_COLS = [
    "date",
    "decision",
    "combined_noise_prob",
    "usd_jpy_noise_prob",
    "usd_thb_noise_prob",
    "remit_note",
]
OPTIONAL_COLS = [
    "recommended_action",
    "recommended_reason",
]


def _load_log() -> pd.DataFrame:
    if not DECISION_LOG_PATH.exists():
        raise FileNotFoundError(f"Missing required file: {DECISION_LOG_PATH}")

    df = pd.read_csv(DECISION_LOG_PATH)

    if "date" not in df.columns:
        raise ValueError(f"'date' column missing in {DECISION_LOG_PATH}")

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df = df.sort_values("date").reset_index(drop=True)

    # ensure optional cols exist for backward compatibility
    for c in OPTIONAL_COLS:
        if c not in df.columns:
            df[c] = ""

    return df


def _filter_recent_days(df: pd.DataFrame, days: int) -> pd.DataFrame:
    if days <= 0:
        return df
    # take last N rows by date (log is daily, so this is fine)
    return df.tail(days).reset_index(drop=True)


def _filter_month(df: pd.DataFrame, month_yyyy_mm: str) -> pd.DataFrame:
    # month_yyyy_mm = "YYYY-MM"
    m = month_yyyy_mm.strip()
    if len(m) != 7 or m[4] != "-":
        raise ValueError("--month must be in YYYY-MM format, e.g. 2026-01")

    month_prefix = m  # "YYYY-MM"
    return df[df["date"].str.startswith(month_prefix)].reset_index(drop=True)


def _fmt_pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def _summarize(df: pd.DataFrame) -> Tuple[str, dict]:
    if df.empty:
        return "no_data", {}

    # counts
    decision_counts = df["decision"].value_counts().to_dict()
    total = len(df)
    on = int(decision_counts.get("ON", 0))
    warn = int(decision_counts.get("WARN", 0))
    off = int(decision_counts.get("OFF", 0))

    avg_noise = float(df["combined_noise_prob"].mean()) if "combined_noise_prob" in df.columns else float("nan")

    # recommended_action breakdown (if present)
    action_counts = {}
    if "recommended_action" in df.columns:
        action_counts = df["recommended_action"].replace({pd.NA: "", None: ""}).value_counts().to_dict()
        # drop empty key if exists
        if "" in action_counts:
            action_counts.pop("", None)

    # dominance (USDJPY vs USDTHB) where available
    dominance = None
    if "usd_jpy_noise_prob" in df.columns and "usd_thb_noise_prob" in df.columns:
        thb_dom = (df["usd_thb_noise_prob"] > df["usd_jpy_noise_prob"]).mean()
        dominance = {"usdthb_dominant_ratio": float(thb_dom)}

    payload = {
        "total": total,
        "ON": on,
        "WARN": warn,
        "OFF": off,
        "avg_noise": avg_noise,
        "action_counts": action_counts,
        "dominance": dominance,
        "date_min": df["date"].min(),
        "date_max": df["date"].max(),
    }
    return "ok", payload


def _print_report(title: str, payload: dict) -> None:
    if not payload:
        print(f"{title}: (no data)")
        return

    total = payload["total"]
    on = payload["ON"]
    warn = payload["WARN"]
    off = payload["OFF"]
    avg_noise = payload["avg_noise"]

    print("=" * 72)
    print(title)
    print("-" * 72)
    print(f"range: {payload['date_min']} .. {payload['date_max']} (days={total})")
    print(f"counts: ON={on} / WARN={warn} / OFF={off}")
    if total > 0:
        print(f"ratio : ON={_fmt_pct(on/total)} / WARN={_fmt_pct(warn/total)} / OFF={_fmt_pct(off/total)}")
    print(f"avg_noise: {avg_noise:.3f}")
    print("-" * 72)

    # action breakdown
    action_counts = payload.get("action_counts") or {}
    if action_counts:
        print("recommended_action breakdown:")
        # show top 10
        for k, v in sorted(action_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]:
            print(f"  - {k}: {v}")
        print("-" * 72)

    # dominance
    dom = payload.get("dominance")
    if dom and "usdthb_dominant_ratio" in dom:
        r = dom["usdthb_dominant_ratio"]
        print(f"dominance: USDTHB noise dominant on {r*100:.1f}% of days")
        print("-" * 72)

    # heuristic one-liner
    one_liner = None
    if avg_noise < 0.45:
        one_liner = "総評: 基本は送ってOK（ノイズ低め）"
    elif avg_noise < 0.60:
        one_liner = "総評: WARN多め。分割運用（半額/小分け）が効く"
    else:
        one_liner = "総評: 高ノイズ月。見送り・待ち重視"
    print(one_liner)
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize JPY→THB remittance decision log.")
    parser.add_argument("--days", type=int, default=30, help="Recent days to summarize (default: 30). Ignored if --month is used.")
    parser.add_argument(
        "--month",
        nargs="?",
        const="__CURRENT__",
        default=None,
        help="Monthly report. Provide YYYY-MM (e.g., 2026-01). If omitted value, uses current month.",
    )
    args = parser.parse_args()

    df = _load_log()

    if args.month is not None:
        if args.month == "__CURRENT__":
            m = date.today().strftime("%Y-%m")
        else:
            m = args.month
        df2 = _filter_month(df, m)
        status, payload = _summarize(df2)
        _print_report(f"FX Remittance Monthly Summary ({m})", payload)
        return 0

    # recent days
    df2 = _filter_recent_days(df, args.days)
    status, payload = _summarize(df2)
    _print_report(f"FX Remittance Recent Summary (last {len(df2)} days)", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
