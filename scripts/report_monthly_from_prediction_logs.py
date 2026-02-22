#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Report MONTHLY performance from persisted prediction logs.

- Input:  analysis/prediction_logs/prediction_log_YYYY-MM-DD.json
- Output: analysis/prediction_reports/monthly_trend3_fx_latest.json/csv

Schema-safe:
- supports legacy: {meta, summary, details}
- supports v1:     {schema_version, prediction:{meta, summary, details}}

Return model:
- per row return = exp * delta
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
    name = p.name
    if not name.startswith("prediction_log_") or not name.endswith(".json"):
        return None
    core = name[len("prediction_log_"):-len(".json")]
    if len(core) != 10 or core[4] != "-" or core[7] != "-":
        return None
    return core


def month_of_day(day: str) -> str:
    # YYYY-MM-DD -> YYYY-MM
    return day[:7]


def unwrap_prediction_root(doc: Dict[str, Any]) -> Dict[str, Any]:
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
    n = len(returns)
    if n < 2:
        return None
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if var <= 0:
        return None
    import math
    return float(mean / math.sqrt(var) * math.sqrt(n))


def load_one_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(p: Path, obj: Dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


@dataclass
class MonthRow:
    month: str
    days_total: int
    days_with_trades: int
    call_rate_by_day: Optional[float]
    trades_total: int
    wins_total: int
    losses_total: int
    win_rate_total: Optional[float]
    total_return: float
    avg_return_per_trade: Optional[float]
    profit_factor_month: Optional[float]
    monthly_sharpe_like: Optional[float]
    monthly_max_drawdown: float
    curve: List[Dict[str, Any]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-dir", default="analysis/prediction_logs", help="prediction_logs directory")
    ap.add_argument("--out-dir", default="analysis/prediction_reports", help="prediction_reports directory")
    ap.add_argument("--limit", type=int, default=365, help="max days to include (newest first)")
    args = ap.parse_args()

    log_dir = Path(args.log_dir)
    out_dir = Path(args.out_dir)
    out_json = out_dir / "monthly_trend3_fx_latest.json"
    out_csv = out_dir / "monthly_trend3_fx_latest.csv"

    if not log_dir.exists():
        payload = {
            "report_schema_version": 2,
            "generated_at_utc": utc_now_iso(),
            "months": [],
        }
        write_json(out_json, payload)
        out_dir.mkdir(parents=True, exist_ok=True)
        with out_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=[
                "month","days_total","days_with_trades","call_rate_by_day",
                "trades_total","wins_total","losses_total","win_rate_total",
                "total_return","avg_return_per_trade","profit_factor_month",
                "monthly_sharpe_like","monthly_max_drawdown","curve_len",
            ])
            w.writeheader()
        print("[OK] monthly report generated (log-dir missing)")
        print(" months=0")
        print(f" out_json={out_json.resolve()}")
        print(f" out_csv ={out_csv.resolve()}")
        return 0

    files = sorted(log_dir.glob("prediction_log_*.json"))
    dated: List[Tuple[str, Path]] = []
    for p in files:
        d = parse_date_from_filename(p)
        if d:
            dated.append((d, p))

    dated.sort(key=lambda x: x[0], reverse=True)
    dated = dated[: max(0, int(args.limit))]
    dated.sort(key=lambda x: x[0])  # chronological

    # Accumulate per month
    month_to_days: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
    for day, p in dated:
        try:
            doc = load_one_json(p)
        except Exception:
            continue
        m = month_of_day(day)
        month_to_days.setdefault(m, []).append((day, doc))

    months_out: List[MonthRow] = []

    for m in sorted(month_to_days.keys()):
        day_docs = month_to_days[m]

        days_total = len(day_docs)

        # Day-level call_rate accumulation
        day_call_rates: List[float] = []
        days_with_trades = 0

        # Month totals
        trades_total = 0
        wins_total = 0
        losses_total = 0
        total_return = 0.0

        # For PF and Sharpe
        realized_trade_returns: List[float] = []
        pos_sum = 0.0
        neg_sum = 0.0

        # Month equity curve
        curve: List[Dict[str, Any]] = []
        eq = 0.0
        eq_series: List[float] = []

        for day, doc in day_docs:
            pred = unwrap_prediction_root(doc)
            details = pred.get("details", [])
            if details is None:
                details = []
            if not isinstance(details, list):
                details = []

            # per day calls/no_call from exp and ok
            day_rows = 0
            day_calls = 0

            day_has_trade = False

            for item in details:
                if not isinstance(item, dict):
                    continue
                day_rows += 1
                exp = safe_int(item.get("exp"), 0)
                ok = item.get("ok", None)
                delta = safe_float(item.get("delta"), 0.0)

                # call accounting
                if exp != 0 and ok is not None:
                    day_calls += 1
                    trades_total += 1
                    day_has_trade = True
                    r = float(exp) * float(delta)
                    realized_trade_returns.append(r)

                    if ok is True:
                        wins_total += 1
                    else:
                        losses_total += 1

                    if r >= 0:
                        pos_sum += r
                    else:
                        neg_sum += (-r)

                # equity always updated by exp*delta (exp=0 -> 0)
                r_row = float(exp) * float(delta)
                total_return += r_row
                eq += r_row
                eq_series.append(eq)
                curve.append({"date": item.get("date", None), "equity": eq})

            if day_has_trade:
                days_with_trades += 1

            if day_rows > 0:
                day_call_rates.append(day_calls / day_rows)

        call_rate_by_day = (sum(day_call_rates) / len(day_call_rates)) if day_call_rates else None
        win_rate_total = (wins_total / trades_total) if trades_total > 0 else None
        avg_return_per_trade = (sum(realized_trade_returns) / len(realized_trade_returns)) if realized_trade_returns else None

        profit_factor = None
        if neg_sum > 0:
            profit_factor = pos_sum / neg_sum
        elif pos_sum > 0 and neg_sum == 0:
            profit_factor = float("inf")  # no losing trades

        m_sharpe = sharpe_like(realized_trade_returns)
        m_max_dd = compute_max_drawdown(eq_series)

        months_out.append(MonthRow(
            month=m,
            days_total=days_total,
            days_with_trades=days_with_trades,
            call_rate_by_day=float(call_rate_by_day) if call_rate_by_day is not None else None,
            trades_total=trades_total,
            wins_total=wins_total,
            losses_total=losses_total,
            win_rate_total=float(win_rate_total) if win_rate_total is not None else None,
            total_return=float(total_return),
            avg_return_per_trade=float(avg_return_per_trade) if avg_return_per_trade is not None else None,
            profit_factor_month=profit_factor if profit_factor is not None else None,
            monthly_sharpe_like=m_sharpe,
            monthly_max_drawdown=float(m_max_dd),
            curve=curve,
        ))

    payload = {
        "report_schema_version": 2,
        "generated_at_utc": utc_now_iso(),
        "months": [
            {
                "month": r.month,
                "days_total": r.days_total,
                "days_with_trades": r.days_with_trades,
                "call_rate_by_day": r.call_rate_by_day,
                "trades_total": r.trades_total,
                "wins_total": r.wins_total,
                "losses_total": r.losses_total,
                "win_rate_total": r.win_rate_total,
                "total_return": r.total_return,
                "avg_return_per_trade": r.avg_return_per_trade,
                "profit_factor_month": r.profit_factor_month,
                "monthly_sharpe_like": r.monthly_sharpe_like,
                "monthly_max_drawdown": r.monthly_max_drawdown,
                "curve": r.curve,
            }
            for r in months_out
        ],
    }

    write_json(out_json, payload)

    out_dir.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "month","days_total","days_with_trades","call_rate_by_day",
            "trades_total","wins_total","losses_total","win_rate_total",
            "total_return","avg_return_per_trade","profit_factor_month",
            "monthly_sharpe_like","monthly_max_drawdown","curve_len",
        ])
        w.writeheader()
        for r in months_out:
            w.writerow({
                "month": r.month,
                "days_total": r.days_total,
                "days_with_trades": r.days_with_trades,
                "call_rate_by_day": r.call_rate_by_day,
                "trades_total": r.trades_total,
                "wins_total": r.wins_total,
                "losses_total": r.losses_total,
                "win_rate_total": r.win_rate_total,
                "total_return": r.total_return,
                "avg_return_per_trade": r.avg_return_per_trade,
                "profit_factor_month": r.profit_factor_month,
                "monthly_sharpe_like": r.monthly_sharpe_like,
                "monthly_max_drawdown": r.monthly_max_drawdown,
                "curve_len": len(r.curve),
            })

    print("[OK] monthly report generated")
    print(f" months={len(months_out)}")
    print(f" out_json={out_json.resolve()}")
    print(f" out_csv ={out_csv.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())