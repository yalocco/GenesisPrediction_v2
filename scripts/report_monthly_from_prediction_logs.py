# scripts/report_monthly_from_prediction_logs.py
#
# Monthly report from analysis/prediction_logs/prediction_log_YYYY-MM-DD.json
#
# Robust against schema drift:
#   - details may be a list (schema v1) or a dict wrapper {"rows":[...]}
#
# Computes per-month:
#   days_total, days_with_trades, call_rate_by_day
#   trades_total, wins_total, losses_total, win_rate_total
#   total_return, avg_return_per_trade, profit_factor_month
#   monthly_sharpe_like, monthly_max_drawdown
#
# Output:
#   analysis/prediction_reports/monthly_trend3_fx_latest.json
#   analysis/prediction_reports/monthly_trend3_fx_latest.csv
#
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_DIR = REPO_ROOT / "analysis" / "prediction_logs"
DEFAULT_OUT_DIR = REPO_ROOT / "analysis" / "prediction_reports"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def safe_int(x: Any) -> Optional[int]:
    try:
        if x is None:
            return None
        return int(x)
    except Exception:
        return None


def parse_date_yyyy_mm_dd(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_details_rows(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    prediction_log schema examples:
      - schema v1:
          { ..., "details": [ {..}, {..}, ... ] }
      - older wrapper variants:
          { ..., "details": {"rows":[...]} }
    """
    details = doc.get("details", [])
    if isinstance(details, list):
        return [r for r in details if isinstance(r, dict)]
    if isinstance(details, dict):
        rows = details.get("rows", [])
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict)]
    return []


def trade_return(row: Dict[str, Any]) -> Optional[float]:
    """
    Treat as "trade" only when:
      - ok is True/False (not None)
      - exp is +1/-1 (not 0)
      - delta is float
    Return definition:
      ret = exp * delta
    """
    ok = row.get("ok", None)
    if ok is None:
        return None

    exp = safe_int(row.get("exp", None))
    if exp is None or exp == 0:
        return None

    delta = safe_float(row.get("delta", None))
    if delta is None:
        return None

    return float(exp) * float(delta)


def max_drawdown(returns: List[float]) -> float:
    if not returns:
        return 0.0
    equity = 0.0
    peak = 0.0
    mdd = 0.0
    for r in returns:
        equity += r
        if equity > peak:
            peak = equity
        dd = peak - equity
        if dd > mdd:
            mdd = dd
    return float(mdd)


def sharpe_like(returns: List[float]) -> Optional[float]:
    # mean/std * sqrt(n)
    if len(returns) < 2:
        return None
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(var)
    if std == 0.0:
        return None
    return float(mean / std * math.sqrt(len(returns)))


def profit_factor(returns: List[float]) -> Optional[float]:
    pos = sum(r for r in returns if r > 0)
    neg = -sum(r for r in returns if r < 0)
    if neg == 0.0:
        if pos == 0.0:
            return None
        return float("inf")
    return float(pos / neg)


@dataclass
class DayAgg:
    day: str
    month: str
    trade_returns: List[float]


def load_prediction_logs(log_dir: Path) -> List[DayAgg]:
    if not log_dir.exists():
        return []

    paths = sorted(log_dir.glob("prediction_log_*.json"))
    out: List[DayAgg] = []

    for p in paths:
        try:
            doc = load_json(p)
        except Exception:
            continue

        day = p.stem.replace("prediction_log_", "")
        try:
            dt = parse_date_yyyy_mm_dd(day)
        except Exception:
            # fallback: skip invalid filename
            continue

        rows = extract_details_rows(doc)
        rets: List[float] = []
        for r in rows:
            tr = trade_return(r)
            if tr is None:
                continue
            rets.append(tr)

        out.append(DayAgg(day=day, month=month_key(dt), trade_returns=rets))

    return out


def build_monthly_report(days: List[DayAgg]) -> List[Dict[str, Any]]:
    by_month: Dict[str, List[DayAgg]] = {}
    for d in days:
        by_month.setdefault(d.month, []).append(d)

    report_rows: List[Dict[str, Any]] = []

    for m in sorted(by_month.keys()):
        ds = sorted(by_month[m], key=lambda x: x.day)
        days_total = len(ds)
        days_with_trades = sum(1 for d in ds if len(d.trade_returns) > 0)
        call_rate_by_day = (days_with_trades / days_total) if days_total > 0 else 0.0

        all_rets: List[float] = []
        for d in ds:
            all_rets.extend(d.trade_returns)

        trades_total = len(all_rets)
        wins_total = sum(1 for r in all_rets if r > 0)
        losses_total = sum(1 for r in all_rets if r < 0)
        win_rate_total = (wins_total / trades_total) if trades_total > 0 else None

        total_return = sum(all_rets) if trades_total > 0 else 0.0
        avg_return_per_trade = (total_return / trades_total) if trades_total > 0 else None

        pf = profit_factor(all_rets)
        sh = sharpe_like(all_rets)
        mdd = max_drawdown(all_rets) if trades_total > 0 else 0.0

        report_rows.append(
            {
                "month": m,
                "days_total": days_total,
                "days_with_trades": days_with_trades,
                "call_rate_by_day": float(call_rate_by_day),
                "trades_total": trades_total,
                "wins_total": wins_total,
                "losses_total": losses_total,
                "win_rate_total": float(win_rate_total) if win_rate_total is not None else None,
                "total_return": float(total_return),
                "avg_return_per_trade": float(avg_return_per_trade) if avg_return_per_trade is not None else None,
                "profit_factor_month": (
                    None
                    if pf is None
                    else ("inf" if isinstance(pf, float) and math.isinf(pf) else float(pf))
                ),
                "monthly_sharpe_like": float(sh) if sh is not None else None,
                "monthly_max_drawdown": float(mdd),
            }
        )

    return report_rows


def write_outputs(months: List[Dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    out_json = out_dir / "monthly_trend3_fx_latest.json"
    out_csv = out_dir / "monthly_trend3_fx_latest.csv"

    payload = {
        "report_schema_version": 1,
        "generated_at_utc": utc_now_iso(),
        "months": months,
    }

    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    df = pd.DataFrame(months)
    preferred = [
        "month",
        "days_total",
        "days_with_trades",
        "call_rate_by_day",
        "trades_total",
        "wins_total",
        "losses_total",
        "win_rate_total",
        "total_return",
        "avg_return_per_trade",
        "profit_factor_month",
        "monthly_sharpe_like",
        "monthly_max_drawdown",
    ]
    cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
    df = df[cols]
    df.to_csv(out_csv, index=False, encoding="utf-8")

    print("[OK] monthly report generated")
    print(f" months={len(months)}")
    print(f" out_json={out_json}")
    print(f" out_csv ={out_csv}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-dir", type=str, default=str(DEFAULT_LOG_DIR), help="prediction_logs directory")
    ap.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT_DIR), help="prediction_reports directory")
    args = ap.parse_args()

    log_dir = Path(args.log_dir)
    out_dir = Path(args.out_dir)

    days = load_prediction_logs(log_dir)
    months = build_monthly_report(days)
    write_outputs(months, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())