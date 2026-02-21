#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily report generator from analysis/prediction_logs/prediction_log_YYYY-MM-DD.json

Outputs (fixed names):
- analysis/prediction_reports/daily_trend3_fx_latest.json
- analysis/prediction_reports/daily_trend3_fx_latest.csv

Design notes:
- Uses prediction_log schema_version=1 style:
  { meta, summary, details:[{date,next_date,trend,dir,exp,fx0,fx1,delta,ok}, ...] }
- A "trade" is a detail row where exp != 0 and ok is True/False (ok is not null).
- Trade return is computed as: trade_return = exp * delta
  (So RISK_OFF (-1) turns negative delta into positive return, etc.)
- day_return is sum of trade_return for that day.
- Cumulative metrics are computed in chronological order of log file dates.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = REPO_ROOT / "analysis" / "prediction_logs"
OUT_DIR = REPO_ROOT / "analysis" / "prediction_reports"

OUT_JSON = OUT_DIR / "daily_trend3_fx_latest.json"
OUT_CSV = OUT_DIR / "daily_trend3_fx_latest.csv"

LOG_RE = re.compile(r"^prediction_log_(\d{4}-\d{2}-\d{2})\.json$")


@dataclass(frozen=True)
class DailyRow:
    date: str
    days_total: int

    trades: int
    wins: int
    losses: int
    hit_rate: Optional[float]

    day_return: float
    cumulative_return: float

    cumulative_trades: int
    cumulative_wins: int
    cumulative_losses: int
    cumulative_hit_rate: Optional[float]

    max_drawdown_so_far: float  # absolute drawdown on cumulative_return axis


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _safe_bool_ok(v: Any) -> Optional[bool]:
    # ok can be true/false/null
    if v is True:
        return True
    if v is False:
        return False
    return None


def _to_int_exp(v: Any) -> int:
    # exp should be -1/0/1, but be forgiving
    try:
        return int(v)
    except Exception:
        return 0


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _list_log_files(log_dir: Path) -> List[Tuple[str, Path]]:
    items: List[Tuple[str, Path]] = []
    if not log_dir.exists():
        return items
    for p in log_dir.iterdir():
        if not p.is_file():
            continue
        m = LOG_RE.match(p.name)
        if not m:
            continue
        date = m.group(1)
        items.append((date, p))
    items.sort(key=lambda x: x[0])
    return items


def _summarize_one_log(date: str, path: Path) -> Tuple[int, int, int, float]:
    """
    Returns: (trades, wins, losses, day_return)

    trade criteria:
      exp != 0 AND ok is not null
    day_return:
      sum(exp * delta) over trades
    wins/losses:
      ok True/False counts
    """
    j = _read_json(path)

    details = j.get("details", [])
    trades = 0
    wins = 0
    losses = 0
    day_return = 0.0

    if isinstance(details, list):
        for row in details:
            if not isinstance(row, dict):
                continue
            exp = _to_int_exp(row.get("exp", 0))
            ok = _safe_bool_ok(row.get("ok", None))
            if exp == 0 or ok is None:
                continue

            delta = _to_float(row.get("delta", 0.0), 0.0)
            trade_ret = float(exp) * delta

            trades += 1
            day_return += trade_ret
            if ok:
                wins += 1
            else:
                losses += 1

    return trades, wins, losses, day_return


def _hit_rate(wins: int, trades: int) -> Optional[float]:
    if trades <= 0:
        return None
    return wins / float(trades)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _write_csv(path: Path, rows: List[DailyRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "date",
        "trades",
        "wins",
        "losses",
        "hit_rate",
        "day_return",
        "cumulative_return",
        "cumulative_trades",
        "cumulative_wins",
        "cumulative_losses",
        "cumulative_hit_rate",
        "max_drawdown_so_far",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    "date": r.date,
                    "trades": r.trades,
                    "wins": r.wins,
                    "losses": r.losses,
                    "hit_rate": "" if r.hit_rate is None else f"{r.hit_rate:.6f}",
                    "day_return": f"{r.day_return:.12f}",
                    "cumulative_return": f"{r.cumulative_return:.12f}",
                    "cumulative_trades": r.cumulative_trades,
                    "cumulative_wins": r.cumulative_wins,
                    "cumulative_losses": r.cumulative_losses,
                    "cumulative_hit_rate": ""
                    if r.cumulative_hit_rate is None
                    else f"{r.cumulative_hit_rate:.6f}",
                    "max_drawdown_so_far": f"{r.max_drawdown_so_far:.12f}",
                }
            )


def build_daily_report(log_dir: Path) -> Dict[str, Any]:
    log_files = _list_log_files(log_dir)

    days: List[DailyRow] = []
    cum_return = 0.0
    cum_trades = 0
    cum_wins = 0
    cum_losses = 0

    peak = 0.0  # peak of cumulative_return
    max_dd = 0.0

    for i, (date, path) in enumerate(log_files, start=1):
        trades, wins, losses, day_ret = _summarize_one_log(date, path)

        cum_return += day_ret
        cum_trades += trades
        cum_wins += wins
        cum_losses += losses

        # drawdown on cumulative_return axis
        if cum_return > peak:
            peak = cum_return
        dd = peak - cum_return
        if dd > max_dd:
            max_dd = dd

        days.append(
            DailyRow(
                date=date,
                days_total=i,
                trades=trades,
                wins=wins,
                losses=losses,
                hit_rate=_hit_rate(wins, trades),
                day_return=day_ret,
                cumulative_return=cum_return,
                cumulative_trades=cum_trades,
                cumulative_wins=cum_wins,
                cumulative_losses=cum_losses,
                cumulative_hit_rate=_hit_rate(cum_wins, cum_trades),
                max_drawdown_so_far=max_dd,
            )
        )

    payload: Dict[str, Any] = {
        "report_schema_version": 1,
        "generated_at_utc": _utc_now_iso(),
        "log_dir": str(log_dir).replace("\\", "/"),
        "days": [
            {
                "date": r.date,
                "trades": r.trades,
                "wins": r.wins,
                "losses": r.losses,
                "hit_rate": r.hit_rate,
                "day_return": r.day_return,
                "cumulative_return": r.cumulative_return,
                "cumulative_trades": r.cumulative_trades,
                "cumulative_wins": r.cumulative_wins,
                "cumulative_losses": r.cumulative_losses,
                "cumulative_hit_rate": r.cumulative_hit_rate,
                "max_drawdown_so_far": r.max_drawdown_so_far,
            }
            for r in days
        ],
        "summary": {
            "days": len(days),
            "total_trades": cum_trades,
            "total_wins": cum_wins,
            "total_losses": cum_losses,
            "overall_hit_rate": _hit_rate(cum_wins, cum_trades),
            "total_return": cum_return,
            "max_drawdown": max_dd,
        },
    }
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--log-dir",
        type=str,
        default=str(LOG_DIR),
        help="Directory containing prediction_log_YYYY-MM-DD.json files",
    )
    ap.add_argument(
        "--out-dir",
        type=str,
        default=str(OUT_DIR),
        help="Output directory (default: analysis/prediction_reports)",
    )
    args = ap.parse_args()

    log_dir = Path(args.log_dir)
    out_dir = Path(args.out_dir)

    payload = build_daily_report(log_dir)

    # write
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / OUT_JSON.name
    out_csv = out_dir / OUT_CSV.name

    _write_json(out_json, payload)

    # convert payload days -> rows for CSV
    rows: List[DailyRow] = []
    for idx, d in enumerate(payload.get("days", []), start=1):
        if not isinstance(d, dict):
            continue
        rows.append(
            DailyRow(
                date=str(d.get("date", "")),
                days_total=idx,
                trades=int(d.get("trades", 0) or 0),
                wins=int(d.get("wins", 0) or 0),
                losses=int(d.get("losses", 0) or 0),
                hit_rate=d.get("hit_rate", None),
                day_return=float(d.get("day_return", 0.0) or 0.0),
                cumulative_return=float(d.get("cumulative_return", 0.0) or 0.0),
                cumulative_trades=int(d.get("cumulative_trades", 0) or 0),
                cumulative_wins=int(d.get("cumulative_wins", 0) or 0),
                cumulative_losses=int(d.get("cumulative_losses", 0) or 0),
                cumulative_hit_rate=d.get("cumulative_hit_rate", None),
                max_drawdown_so_far=float(d.get("max_drawdown_so_far", 0.0) or 0.0),
            )
        )
    _write_csv(out_csv, rows)

    print("[OK] daily report generated")
    print(f" days={len(rows)}")
    print(f" out_json={out_json}")
    print(f" out_csv ={out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())