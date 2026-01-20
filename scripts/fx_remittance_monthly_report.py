"""
fx_remittance_monthly_report.py

目的:
- JPY→THB 仕送り判断ログから、月次レポートを Markdown 形式で保存する
- 同時に CSV も出力する（集計 + 日次一覧）

出力先:
- data/fx/reports/YYYY-MM.md
- data/fx/reports/YYYY-MM_summary.csv
- data/fx/reports/YYYY-MM_daily.csv

実行例:
  python scripts/fx_remittance_monthly_report.py
  python scripts/fx_remittance_monthly_report.py --month 2026-01
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "fx"
LOG_PATH = DATA_DIR / "jpy_thb_remittance_decision_log.csv"
REPORT_DIR = DATA_DIR / "reports"


def _heuristic_overall(avg_noise: float) -> str:
    if avg_noise < 0.45:
        return "基本は送ってOK（ノイズ低）"
    if avg_noise < 0.60:
        return "WARN多め。分割・小分け運用が有効"
    return "高ノイズ月。見送り・待ち重視"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate monthly FX remittance report (Markdown + CSV).")
    parser.add_argument(
        "--month",
        default=None,
        help="Target month in YYYY-MM format. Default: current month.",
    )
    args = parser.parse_args()

    month = args.month or date.today().strftime("%Y-%m")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not LOG_PATH.exists():
        raise FileNotFoundError(f"Missing log: {LOG_PATH}")

    df = pd.read_csv(LOG_PATH)

    if "date" not in df.columns:
        raise ValueError("Log must contain 'date' column")

    # normalize + filter month
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    dfm = df[df["date"].str.startswith(month)].copy()

    if dfm.empty:
        print(f"No data for {month}")
        return 0

    # ----- Summary metrics -----
    total = int(len(dfm))
    counts = dfm["decision"].value_counts()

    # handle missing numeric cols safely
    if "combined_noise_prob" in dfm.columns:
        dfm["combined_noise_prob"] = pd.to_numeric(dfm["combined_noise_prob"], errors="coerce")
        avg_noise = float(dfm["combined_noise_prob"].mean())
    else:
        avg_noise = float("nan")

    action_counts = {}
    if "recommended_action" in dfm.columns:
        action_counts = (
            dfm["recommended_action"]
            .replace({None: "", pd.NA: ""})
            .value_counts()
            .to_dict()
        )
        action_counts.pop("", None)

    thb_dom_ratio = None
    if "usd_thb_noise_prob" in dfm.columns and "usd_jpy_noise_prob" in dfm.columns:
        dfm["usd_thb_noise_prob"] = pd.to_numeric(dfm["usd_thb_noise_prob"], errors="coerce")
        dfm["usd_jpy_noise_prob"] = pd.to_numeric(dfm["usd_jpy_noise_prob"], errors="coerce")
        thb_dom_ratio = float((dfm["usd_thb_noise_prob"] > dfm["usd_jpy_noise_prob"]).mean())

    overall = _heuristic_overall(avg_noise) if avg_noise == avg_noise else "総評: (avg_noise算出不可)"

    # ----- Write Markdown -----
    lines: list[str] = []
    lines.append(f"# FX Remittance Monthly Report ({month})")
    lines.append("")
    lines.append("## 概要")
    lines.append(f"- 対象日数: {total} 日")
    if avg_noise == avg_noise:
        lines.append(f"- 平均ノイズ: {avg_noise:.3f}")
    else:
        lines.append(f"- 平均ノイズ: (N/A)")
    lines.append(f"- 総評: **{overall}**")
    lines.append("")
    lines.append("## 判断内訳")
    for k in ["ON", "WARN", "OFF"]:
        lines.append(f"- {k}: {int(counts.get(k, 0))}")
    lines.append("")

    if action_counts:
        lines.append("## 推奨行動内訳")
        for k, v in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- {k}: {v}")
        lines.append("")

    if thb_dom_ratio is not None:
        lines.append("## ノイズ優勢")
        lines.append(f"- USDTHB側優勢日: {thb_dom_ratio*100:.1f}%")
        lines.append("")

    md_path = REPORT_DIR / f"{month}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    # ----- Write CSV (summary) -----
    summary_rows = [
        {"key": "month", "value": month},
        {"key": "days", "value": total},
        {"key": "avg_noise", "value": "" if avg_noise != avg_noise else f"{avg_noise:.6f}"},
        {"key": "overall", "value": overall},
        {"key": "count_ON", "value": int(counts.get("ON", 0))},
        {"key": "count_WARN", "value": int(counts.get("WARN", 0))},
        {"key": "count_OFF", "value": int(counts.get("OFF", 0))},
    ]
    if thb_dom_ratio is not None:
        summary_rows.append({"key": "usdthb_dominant_ratio", "value": f"{thb_dom_ratio:.6f}"})

    # add action counts as separate keys
    for k, v in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
        summary_rows.append({"key": f"action_{k}", "value": int(v)})

    summary_df = pd.DataFrame(summary_rows)
    summary_csv_path = REPORT_DIR / f"{month}_summary.csv"
    summary_df.to_csv(summary_csv_path, index=False, encoding="utf-8")

    # ----- Write CSV (daily) -----
    # keep stable, human-friendly columns if they exist
    daily_cols_pref = [
        "date",
        "decision",
        "combined_noise_prob",
        "usd_jpy_noise_prob",
        "usd_thb_noise_prob",
        "remit_note",
        "recommended_action",
        "recommended_reason",
    ]
    daily_cols = [c for c in daily_cols_pref if c in dfm.columns]
    daily_df = dfm[daily_cols].copy().sort_values("date").reset_index(drop=True)

    daily_csv_path = REPORT_DIR / f"{month}_daily.csv"
    daily_df.to_csv(daily_csv_path, index=False, encoding="utf-8")

    print(f"[OK] Monthly report saved: {md_path}")
    print(f"[OK] Summary CSV saved:   {summary_csv_path}")
    print(f"[OK] Daily CSV saved:     {daily_csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
