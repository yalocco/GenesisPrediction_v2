# scripts/sweep_threshold_trend3_fx.py
# Threshold sweep for Trend3 FX backtest (research tool)
#
# Run:
#   .\.venv\Scripts\python.exe scripts\sweep_threshold_trend3_fx.py
#   .\.venv\Scripts\python.exe scripts\sweep_threshold_trend3_fx.py --start 2026-01-01 --end 2026-02-18

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from backtest_trend3_fx_v2 import (
    OUT_DIR,
    load_daily_scores,
    load_fx_thb_per_jpy,
    run_backtest,
)


def _ensure_outdir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def sweep_thresholds(
    start: Optional[str],
    end: Optional[str],
    thresholds: List[float],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    scores, diag = load_daily_scores(start=start, end=end)
    fx, fx_source = load_fx_thb_per_jpy()

    rows: List[Dict[str, Any]] = []
    best = None

    for th in thresholds:
        df, meta = run_backtest(scores=scores, fx=fx, threshold=float(th))
        meta["fx_source"] = fx_source
        m = meta["metrics"]
        row = {
            "threshold": float(th),
            "rows_total": int(m["rows_total"]),
            "calls": int(m["calls"]),
            "hit": int(m["hit"]),
            "miss": int(m["miss"]),
            "hit_rate": (float(m["hit_rate"]) if m["hit_rate"] is not None else None),
        }
        rows.append(row)

        # pick best by hit_rate, tie-breaker: more calls, then smaller threshold
        if row["hit_rate"] is None:
            continue
        key = (row["hit_rate"], row["calls"], -row["threshold"])
        if best is None or key > best[0]:
            best = (key, row)

    out_df = pd.DataFrame(rows).sort_values(["hit_rate", "calls"], ascending=[False, False], na_position="last")

    meta_out: Dict[str, Any] = {
        "run_local": datetime.now().isoformat(timespec="seconds"),
        "start": start,
        "end": end,
        "fx_source": fx_source,
        "thresholds": thresholds,
        "best": (best[1] if best is not None else None),
        "diag": diag,
    }
    return out_df, meta_out


def write_outputs(df: pd.DataFrame, meta: Dict[str, Any]) -> Tuple[Path, Path, Path]:
    _ensure_outdir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = OUT_DIR / f"threshold_sweep_trend3_fx_{ts}"
    txt_path = base.with_suffix(".txt")
    csv_path = base.with_suffix(".csv")
    json_path = base.with_suffix(".json")

    df.to_csv(csv_path, index=False, encoding="utf-8")
    json_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    lines: List[str] = []
    lines.append("GenesisPrediction v2 - Threshold Sweep (Trend3 FX)")
    lines.append(f"run_local: {meta['run_local']}")
    lines.append(f"start: {meta['start']}")
    lines.append(f"end: {meta['end']}")
    lines.append(f"fx_source: {meta['fx_source']}")
    lines.append("")
    best = meta.get("best")
    if best:
        lines.append(f"[BEST] threshold={best['threshold']} calls={best['calls']} hit={best['hit']} miss={best['miss']} hit_rate={best['hit_rate']}")
    else:
        lines.append("[BEST] none")
    lines.append("")
    lines.append("TOP 10 (by hit_rate desc, calls desc)")
    top = df.head(10).to_dict(orient="records")
    for r in top:
        lines.append(f"- th={r['threshold']:.3f} calls={int(r['calls'])} hit={int(r['hit'])} miss={int(r['miss'])} hit_rate={r['hit_rate']}")
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return txt_path, csv_path, json_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=str, default=None)
    ap.add_argument("--end", type=str, default=None)
    ap.add_argument("--min", dest="min_th", type=float, default=0.00)
    ap.add_argument("--max", dest="max_th", type=float, default=0.20)
    ap.add_argument("--step", type=float, default=0.01)
    args = ap.parse_args()

    thresholds: List[float] = []
    th = float(args.min_th)
    while th <= float(args.max_th) + 1e-12:
        thresholds.append(round(th, 6))
        th += float(args.step)

    df, meta = sweep_thresholds(start=args.start, end=args.end, thresholds=thresholds)
    txt_path, csv_path, json_path = write_outputs(df, meta)

    print("[OK] sweep written:")
    print(" -", txt_path)
    print(" -", csv_path)
    print(" -", json_path)

    best = meta.get("best")
    if best:
        print(f"[BEST] threshold={best['threshold']} calls={best['calls']} hit={best['hit']} miss={best['miss']} hit_rate={best['hit_rate']}")
    else:
        print("[BEST] none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
