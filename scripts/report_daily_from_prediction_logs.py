#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Report DAILY performance from persisted prediction logs.

- Input:  analysis/prediction_logs/prediction_log_YYYY-MM-DD.json
- Output: analysis/prediction_reports/daily_trend3_fx_latest.json/csv

Schema-safe:
- supports legacy: {meta, summary, details}
- supports v1:     {schema_version, prediction:{meta, summary, details}}

Return model:
- per row return = exp * delta
  - exp=0 -> no trade -> return=0 (equity flat)
  - exp=1/-1 -> trade -> signed return
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ----------------------------
# Helpers
# ----------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def safe_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        return int(x)
    except Exception:
        return default


def parse_date_from_filename(p: Path) -> Optional[str]:
    # prediction_log_YYYY-MM-DD.json
    name = p.name
    if not name.startswith("prediction_log_") or not name.endswith(".json"):
        return None
    core = name[len("prediction_log_"):-len(".json")]
    # quick validate YYYY-MM-DD
    if len(core) != 10 or core[4] != "-" or core[7] != "-":
        return None
    return core


def unwrap_prediction_root(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a dict that contains meta/summary/details.
    - legacy: doc already has them
    - v1: doc["prediction"] has them
    """
    pred = doc.get("prediction")
    if isinstance(pred, dict):
        return pred
    return doc


def compute_max_drawdown(equity: List[float]) -> float:
    if not equity:
        return 0.0
    peak = equity[0]
    max_dd = 0.0
    for v in equity:
        if v > peak:
            peak = v
        dd = peak - v
        if dd > max_dd:
            max_dd = dd
    return float(max_dd)


def sharpe_like(returns: List[float]) -> Optional[float]:
    # simple: mean/std * sqrt(n)
    n = len(returns)
    if n < 2:
        return None
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if var <= 0:
        return None
    import math
    return float(mean / math.sqrt(var) * math.sqrt(n))


@dataclass
class DayReport:
    day: str
    threshold: Optional[float]
    fx_strategy: Optional[str]
    notes: Optional[str]
    rows: int
    calls: int
    hit: int
    miss: int
    no_call: int
    call_rate: Optional[float]
    hit_rate: Optional[float]
    total_return: float
    avg_return_per_row: Optional[float]
    equity_curve: List[Dict[str, Any]]
    max_drawdown: float
    daily_sharpe_like: Optional[float]


def build_day_report(day: str, doc: Dict[str, Any]) -> DayReport:
    pred = unwrap_prediction_root(doc)

    meta = pred.get("meta", {}) if isinstance(pred.get("meta"), dict) else {}
    details = pred.get("details", [])
    if details is None:
        details = []
    if not isinstance(details, list):
        # if corrupted, treat as empty
        details = []

    rows = len(details)

    # calls/hit/miss/no_call from ok & exp
    calls = 0
    hit = 0
    miss = 0
    no_call = 0

    # returns
    trade_returns: List[float] = []
    equity_curve: List[Dict[str, Any]] = []
    eq = 0.0
    eq_series: List[float] = []

    for item in details:
        if not isinstance(item, dict):
            continue
        exp = safe_int(item.get("exp"), 0)
        ok = item.get("ok", None)

        # count
        if exp == 0 or ok is None:
            no_call += 1
        else:
            calls += 1
            if ok is True:
                hit += 1
            else:
                miss += 1

        delta = safe_float(item.get("delta"), 0.0)
        r = float(exp) * float(delta)
        # record per-row return (including 0 if exp==0)
        trade_returns.append(r)

        eq += r
        eq_series.append(eq)
        equity_curve.append({"date": item.get("date", None), "equity": eq})

    call_rate = (calls / rows) if rows > 0 else None
    hit_rate = (hit / calls) if calls > 0 else None
    total_return = float(sum(trade_returns)) if trade_returns else 0.0
    avg_return_per_row = (total_return / rows) if rows > 0 else None
    max_dd = compute_max_drawdown(eq_series)

    # sharpe-like only on actual trades (exp!=0)
    realized = []
    for item in details:
        if not isinstance(item, dict):
            continue
        exp = safe_int(item.get("exp"), 0)
        if exp == 0:
            continue
        realized.append(float(exp) * safe_float(item.get("delta"), 0.0))
    d_sharpe = sharpe_like(realized)

    threshold = meta.get("threshold", None)
    fx_strategy = meta.get("fx_strategy", None)
    notes = meta.get("notes", None)

    threshold_f = None
    if threshold is not None:
        try:
            threshold_f = float(threshold)
        except Exception:
            threshold_f = None

    return DayReport(
        day=day,
        threshold=threshold_f,
        fx_strategy=str(fx_strategy) if fx_strategy is not None else None,
        notes=str(notes) if notes is not None else None,
        rows=rows,
        calls=calls,
        hit=hit,
        miss=miss,
        no_call=no_call,
        call_rate=float(call_rate) if call_rate is not None else None,
        hit_rate=float(hit_rate) if hit_rate is not None else None,
        total_return=total_return,
        avg_return_per_row=float(avg_return_per_row) if avg_return_per_row is not None else None,
        equity_curve=equity_curve,
        max_drawdown=float(max_dd),
        daily_sharpe_like=d_sharpe,
    )


def load_one_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(p: Path, obj: Dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_csv(p: Path, days: List[DayReport]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "day",
        "threshold",
        "fx_strategy",
        "rows",
        "calls",
        "hit",
        "miss",
        "no_call",
        "call_rate",
        "hit_rate",
        "total_return",
        "avg_return_per_row",
        "max_drawdown",
        "daily_sharpe_like",
        "equity_curve_len",
        "notes",
    ]
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for d in days:
            w.writerow({
                "day": d.day,
                "threshold": d.threshold,
                "fx_strategy": d.fx_strategy,
                "rows": d.rows,
                "calls": d.calls,
                "hit": d.hit,
                "miss": d.miss,
                "no_call": d.no_call,
                "call_rate": d.call_rate,
                "hit_rate": d.hit_rate,
                "total_return": d.total_return,
                "avg_return_per_row": d.avg_return_per_row,
                "max_drawdown": d.max_drawdown,
                "daily_sharpe_like": d.daily_sharpe_like,
                "equity_curve_len": len(d.equity_curve),
                "notes": d.notes,
            })


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-dir", default="analysis/prediction_logs", help="prediction_logs directory")
    ap.add_argument("--out-dir", default="analysis/prediction_reports", help="prediction_reports directory")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (if set, only that day)")
    ap.add_argument("--limit", type=int, default=90, help="max days to include (newest first)")
    args = ap.parse_args()

    log_dir = Path(args.log_dir)
    out_dir = Path(args.out_dir)
    out_json = out_dir / "daily_trend3_fx_latest.json"
    out_csv = out_dir / "daily_trend3_fx_latest.csv"

    if not log_dir.exists():
        # generate empty but valid artifact
        payload = {
            "report_schema_version": 2,
            "generated_at_utc": utc_now_iso(),
            "days": [],
        }
        write_json(out_json, payload)
        write_csv(out_csv, [])
        print("[OK] daily report generated (log-dir missing)")
        print(" days=0")
        print(f" out_json={out_json.resolve()}")
        print(f" out_csv ={out_csv.resolve()}")
        return 0

    files = sorted(log_dir.glob("prediction_log_*.json"))
    # keep only valid date files
    dated: List[Tuple[str, Path]] = []
    for p in files:
        d = parse_date_from_filename(p)
        if d:
            dated.append((d, p))

    # filter date if requested
    if args.date:
        dated = [(d, p) for (d, p) in dated if d == args.date]

    # newest first then limit, but reports should be chronological in output
    dated.sort(key=lambda x: x[0], reverse=True)
    dated = dated[: max(0, int(args.limit))]
    dated.sort(key=lambda x: x[0])

    reports: List[DayReport] = []
    for day, p in dated:
        try:
            doc = load_one_json(p)
        except Exception:
            # skip unreadable
            continue
        reports.append(build_day_report(day, doc))

    payload = {
        "report_schema_version": 2,
        "generated_at_utc": utc_now_iso(),
        "days": [
            {
                "day": r.day,
                "meta": {
                    "threshold": r.threshold,
                    "fx_strategy": r.fx_strategy,
                    "notes": r.notes,
                },
                "summary": {
                    "rows": r.rows,
                    "calls": r.calls,
                    "hit": r.hit,
                    "miss": r.miss,
                    "no_call": r.no_call,
                    "call_rate": r.call_rate,
                    "hit_rate": r.hit_rate,
                    "total_return": r.total_return,
                    "avg_return_per_row": r.avg_return_per_row,
                    "equity_curve_len": len(r.equity_curve),
                    "max_drawdown": r.max_drawdown,
                    "daily_sharpe_like": r.daily_sharpe_like,
                },
                "equity_curve": r.equity_curve,
            }
            for r in reports
        ],
    }

    write_json(out_json, payload)
    write_csv(out_csv, reports)

    print("[OK] daily report generated")
    print(f" days={len(reports)}")
    print(f" out_json={out_json.resolve()}")
    print(f" out_csv ={out_csv.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())