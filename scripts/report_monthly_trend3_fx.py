# scripts/report_monthly_trend3_fx.py
# Monthly report for Trend3 FX backtests (reads existing CSV logs)
#
# Purpose:
#   Aggregate backtest results by month to reduce randomness and validate stability.
#
# Input:
#   analysis/prediction_backtests/trend3_fx_v2A_*.csv
#   (default pattern can be overridden)
#
# Output:
#   analysis/prediction_backtests/monthly_report_trend3_fx_YYYYMMDD_HHMMSS.{txt,csv,json}
#
# Run:
#   .\.venv\Scripts\python.exe scripts\report_monthly_trend3_fx.py
#   .\.venv\Scripts\python.exe scripts\report_monthly_trend3_fx.py --pattern "trend3_fx_v2A_*.csv"
#   .\.venv\Scripts\python.exe scripts\report_monthly_trend3_fx.py --limit 50
#
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = REPO_ROOT / "analysis"
BT_DIR = ANALYSIS_DIR / "prediction_backtests"


REQUIRED_COLS = {"date", "outcome"}
OPTIONAL_COLS = {"hit", "uncertainty", "trend3", "direction", "delta_next", "net", "risk", "positive"}


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if pd.isna(v):
            return None
        return v
    except Exception:
        return None


def read_backtest_csv(path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    dbg: Dict[str, Any] = {"path": str(path)}
    df = pd.read_csv(path)

    dbg["columns"] = list(df.columns)

    missing = sorted(list(REQUIRED_COLS - set(df.columns)))
    if missing:
        dbg["error"] = f"missing_required_cols={missing}"
        return pd.DataFrame(), dbg

    # normalize date
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).copy()
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # normalize outcome
    df["outcome"] = df["outcome"].astype(str)

    # add month
    df["month"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m")
    df = df.dropna(subset=["month"]).copy()

    # ensure hit column
    if "hit" not in df.columns:
        # derive from outcome when possible
        df["hit"] = df["outcome"].map(lambda x: 1 if x == "HIT" else (0 if x == "MISS" else pd.NA))

    # coerce numeric columns that may exist
    for c in OPTIONAL_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    dbg["rows"] = int(len(df))
    dbg["min_date"] = (df["date"].min() if len(df) else None)
    dbg["max_date"] = (df["date"].max() if len(df) else None)
    return df, dbg


def outcome_counts(g: pd.DataFrame) -> Dict[str, int]:
    vc = g["outcome"].value_counts(dropna=False).to_dict()
    return {
        "HIT": int(vc.get("HIT", 0)),
        "MISS": int(vc.get("MISS", 0)),
        "NO_CALL": int(vc.get("NO_CALL", 0)),
    }


def agg_month(g: pd.DataFrame) -> Dict[str, Any]:
    counts = outcome_counts(g)
    calls = counts["HIT"] + counts["MISS"]
    hit_rate = (counts["HIT"] / calls) if calls > 0 else None

    # uncertainty stats
    unc_mean = safe_float(g["uncertainty"].mean()) if "uncertainty" in g.columns else None
    unc_p50 = safe_float(g["uncertainty"].median()) if "uncertainty" in g.columns else None
    unc_max = safe_float(g["uncertainty"].max()) if "uncertainty" in g.columns else None

    # trend3 stats
    tr_mean = safe_float(g["trend3"].mean()) if "trend3" in g.columns else None
    tr_abs_mean = safe_float(g["trend3"].abs().mean()) if "trend3" in g.columns else None

    return {
        "month": str(g["month"].iloc[0]),
        "rows": int(len(g)),
        "calls": int(calls),
        "hit": int(counts["HIT"]),
        "miss": int(counts["MISS"]),
        "no_call": int(counts["NO_CALL"]),
        "hit_rate": hit_rate,
        "unc_mean": unc_mean,
        "unc_p50": unc_p50,
        "unc_max": unc_max,
        "trend3_mean": tr_mean,
        "trend3_abs_mean": tr_abs_mean,
    }


def write_outputs(monthly_df: pd.DataFrame, meta: Dict[str, Any]) -> Dict[str, str]:
    BT_DIR.mkdir(parents=True, exist_ok=True)
    ts = now_ts()
    base = BT_DIR / f"monthly_report_trend3_fx_{ts}"

    p_csv = str(base.with_suffix(".csv"))
    p_json = str(base.with_suffix(".json"))
    p_txt = str(base.with_suffix(".txt"))

    monthly_df.to_csv(p_csv, index=False)

    payload = {"meta": meta, "monthly": monthly_df.to_dict(orient="records")}
    Path(p_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # human-readable txt
    lines: List[str] = []
    lines.append("Monthly report: Trend3 FX backtests")
    lines.append(f"generated_at_local: {meta.get('generated_at_local')}")
    lines.append(f"repo_root: {meta.get('repo_root')}")
    lines.append(f"pattern: {meta.get('pattern')}")
    lines.append(f"files_used: {meta.get('files_used')}")
    lines.append("")

    if len(monthly_df) == 0:
        lines.append("No data.")
    else:
        # overall
        total_calls = int(monthly_df["calls"].sum())
        total_hit = int(monthly_df["hit"].sum())
        total_miss = int(monthly_df["miss"].sum())
        overall_rate = (total_hit / total_calls) if total_calls else None
        lines.append(f"OVERALL: calls={total_calls} hit={total_hit} miss={total_miss} hit_rate={overall_rate}")
        lines.append("")

        # table
        cols = ["month", "calls", "hit", "miss", "hit_rate", "no_call", "unc_mean", "unc_max", "trend3_abs_mean"]
        lines.append("BY MONTH:")
        lines.append(",".join(cols))
        for _, r in monthly_df.sort_values("month").iterrows():
            row = []
            for c in cols:
                v = r.get(c)
                if isinstance(v, float):
                    row.append("" if pd.isna(v) else f"{v:.6f}")
                else:
                    row.append("" if v is None else str(v))
            lines.append(",".join(row))

    Path(p_txt).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"csv": p_csv, "json": p_json, "txt": p_txt}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="trend3_fx_v2A_*.csv")
    ap.add_argument("--limit", type=int, default=0, help="0=all files, otherwise use newest N files")
    ap.add_argument("--min-month-calls", type=int, default=1, help="months with calls < N are kept but can be inspected")
    args = ap.parse_args()

    if not BT_DIR.exists():
        raise RuntimeError(f"missing dir: {BT_DIR}")

    files = sorted(BT_DIR.glob(args.pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    debug_files: List[Dict[str, Any]] = []
    dfs: List[pd.DataFrame] = []

    for p in files:
        df, dbg = read_backtest_csv(p)
        debug_files.append(dbg)
        if len(df):
            df["source_file"] = p.name
            dfs.append(df)

    if not dfs:
        # write debug anyway
        meta = {
            "generated_at_local": datetime.now().isoformat(timespec="seconds"),
            "repo_root": str(REPO_ROOT),
            "pattern": args.pattern,
            "files_used": 0,
            "files_debug": debug_files[:50],
        }
        out = write_outputs(pd.DataFrame(), meta)
        print("[WARN] no usable CSV found")
        print("[OK] report written:")
        print(" -", out["txt"])
        print(" -", out["csv"])
        print(" -", out["json"])
        return 0

    all_df = pd.concat(dfs, ignore_index=True)

    # aggregate
    monthly_rows: List[Dict[str, Any]] = []
    for m, g in all_df.groupby("month"):
        row = agg_month(g)
        monthly_rows.append(row)

    monthly_df = pd.DataFrame(monthly_rows)
    monthly_df = monthly_df.sort_values("month").reset_index(drop=True)

    # optional info column: flag low-calls months
    monthly_df["low_calls"] = monthly_df["calls"] < int(args.min_month_calls)

    meta = {
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "pattern": args.pattern,
        "files_used": int(len(files)),
        "limit": int(args.limit),
        "min_month_calls": int(args.min_month_calls),
        "files_debug_sample": debug_files[:10],
        "total_rows": int(len(all_df)),
        "months": int(len(monthly_df)),
    }

    out = write_outputs(monthly_df, meta)

    # console summary
    total_calls = int(monthly_df["calls"].sum())
    total_hit = int(monthly_df["hit"].sum())
    total_miss = int(monthly_df["miss"].sum())
    overall_rate = (total_hit / total_calls) if total_calls else None

    print("[OK] report written:")
    print(" -", out["txt"])
    print(" -", out["csv"])
    print(" -", out["json"])
    print(f"[SUMMARY] months={len(monthly_df)} overall_calls={total_calls} hit={total_hit} miss={total_miss} hit_rate={overall_rate}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
